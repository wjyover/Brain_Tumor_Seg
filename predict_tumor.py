import SimpleITK as sitk
from batchgenerators.augmentations.utils import resize_segmentation
from nnunet.training.model_restore import restore_model
from nnunet.inference.pretrained_models.download_pretrained_model import download_file
import numpy as np
import os
def postprocess_segment(segmentation,dct, order=1, force_separate_z=None, order_z=0):
    """
    faster and uses less ram than save_segmentation_nifti_from_softmax, but maybe less precise and also does not support
    softmax export (which is needed for ensembling). So it's a niche function that may be useful in some cases.
    :param segmentation:
    :param out_fname:
    :param dct:
    :param order:
    :param force_separate_z:
    :return:
    """
    # suppress output
    print("force_separate_z:", force_separate_z, "interpolation order:", order)
    # first resample, then put result into bbox of cropping, then save
    current_shape = segmentation.shape
    shape_original_after_cropping = dct.get('size_after_cropping')
    shape_original_before_cropping = dct.get('original_size_of_raw_data')
    # current_spacing = dct.get('spacing_after_resampling')
    # original_spacing = dct.get('original_spacing')

    if np.any(np.array(current_shape) != np.array(shape_original_after_cropping)):
        seg_old_spacing = resize_segmentation(segmentation, shape_original_after_cropping, order, 0)
    else:
        seg_old_spacing = segmentation

    bbox = dct.get('crop_bbox')

    if bbox is not None:
        seg_old_size = np.zeros(shape_original_before_cropping)
        for c in range(3):
            bbox[c][1] = np.min((bbox[c][0] + seg_old_spacing.shape[c], shape_original_before_cropping[c]))
        seg_old_size[bbox[0][0]:bbox[0][1],
        bbox[1][0]:bbox[1][1],
        bbox[2][0]:bbox[2][1]] = seg_old_spacing
    else:
        seg_old_size = seg_old_spacing

    seg_resized_itk = sitk.GetImageFromArray(seg_old_size.astype(np.uint8))
    seg_resized_itk.SetSpacing(dct['itk_spacing'])
    seg_resized_itk.SetOrigin(dct['itk_origin'])
    seg_resized_itk.SetDirection(dct['itk_direction'])
    return seg_resized_itk
def predict(p,trainer):
    if 'segmentation_export_params' in trainer.plans.keys():
        force_separate_z = trainer.plans['segmentation_export_params']['force_separate_z']
        interpolation_order = trainer.plans['segmentation_export_params']['interpolation_order']
        interpolation_order_z = trainer.plans['segmentation_export_params']['interpolation_order_z']
    else:
        force_separate_z = None
        interpolation_order = 1
        interpolation_order_z = 0
    d,_,dct = trainer.preprocess_patient([p])
    print(d[0].size)
    softmax_mean=trainer.predict_preprocessed_data_return_seg_and_softmax(d,True, trainer.data_aug_params[
        'mirror_axes'], True, step_size=0.5, use_gaussian=True, all_in_gpu=False,
                                                                                mixed_precision=True)[0]
    seg_resized_itk=postprocess_segment(softmax_mean,dct,interpolation_order, force_separate_z=force_separate_z,order_z=interpolation_order_z)
    return seg_resized_itk
def predict_tumor(p):
    checkpoint='./t2_whole.model'
    if not os.path.exists(checkpoint):
        print(checkpoint)
        url='https://1drv.ms/u/s!Agu87mLKyliLhjixVepPZvOYGF-Z?e=b42WD3'
        download_file(url,checkpoint)
    trainer=restore_model(checkpoint+'.pkl',checkpoint)
    whole_tumor=predict(p,trainer)
    sitk.WriteImage(whole_tumor,p.replace('.nii','_whole_tumor.nii'))
    checkpoint='./t2_core.model'
    if not os.path.exists(checkpoint):
        url='https://1drv.ms/u/s!Agu87mLKyliLhjlf9B4ZjxXpy-sB?e=m0jTrB'
        download_file(url,checkpoint)
    trainer=restore_model(checkpoint+'.pkl',checkpoint)
    core_tumor=predict(p,trainer)
    sitk.WriteImage(core_tumor,p.replace('.nii','_core_tumor.nii'))

if __name__=='__main__':
    ori_path='t2.nii.gz' #path to T2 nifty file
    predict_tumor(ori_path) #generate Brain Tumor mask
