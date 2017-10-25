"""
Unet for lung segmentation
"""
import numpy as np
import tensorflow as tf
import neural_network.tf_wrap as tf_wrap
from neural_network.tf_layer import tf_layer

import os
#import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import cv2
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

from keras.preprocessing.image import ImageDataGenerator

# these functions should be defined specifically for individal neural network
# example of the prediction function, defined using tensorflow lib
def tf_prediction_func_unet( model ):
    #if model.arg is None:
    #    model.arg = [1.0, 1.0]
    # get data size
    NNlayer     = tf_layer()
    #data_size   = int(model.data.get_shape()[1])
    #im_shape    = (model.data.shape[1], model.data.shape[2])#(100, 100)#
    #target_size = int(model.target.get_shape()[1])
    pool_len    = 2
    n_features  = 32
    cnn_ksize   = (10,10)
    
    #out_size = data_size#n_features*data_size//(pool_len**4)
    #y1_4d    = tf.reshape(model.data, [-1,im_shape[0],im_shape[1],1]) #reshape into 4d tensor
    # input size   [-1, im_shape[0],          im_shape[1],         1 ]
    # output size  [-1, im_shape[0],          im_shape[1], n_features ]
    conv1_12 = NNlayer.multi_convolution2d(model.data, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (1,          n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0],          im_shape[1],          n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    pool1    = NNlayer.pool(conv1_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv2_12 = NNlayer.multi_convolution2d(pool1, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    pool2    = NNlayer.pool(conv2_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    # output size  [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    up3      = NNlayer.deconvolution2d(pool2, cov_ker_size = ( pool_len, pool_len), \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    merge3   = NNlayer.merge(conv2_12, up3, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv3_12 = NNlayer.multi_convolution2d(merge3, cov_ker_size = (pool_len, pool_len), n_cnn_layers = 3, \
                                           in_n_features_arr  = (2*n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features,   n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0],          im_shape[1],          n_features ]
    up4      = NNlayer.deconvolution2d(conv3_12, cov_ker_size = cnn_ksize, \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0], im_shape[1], n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 2*n_features ]
    merge4   = NNlayer.merge(conv1_12, up4, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0], im_shape[1], 2*n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 1 ]
    conv4_12 = NNlayer.multi_convolution2d(merge4, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (2*n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features,  n_features,   1), \
                                           pool_type = 'None', activate_type = 'sigmoid')
    # input data shape [-1,  data_size/4, 1, cnn_n_feature], output data shape [-1, out_size=n_features*data_size//4]
    #y = tf.reshape(conv4_12, [-1, im_shape[0], im_shape[1]]) #flatten
    # softmax output
    return conv4_12#tf.argmax(conv4_12)

def tf_prediction_func_unet4( model ):
    #if model.arg is None:
    #    model.arg = [1.0, 1.0]
    # get data size
    NNlayer     = tf_layer()
    #data_size   = int(model.data.get_shape()[1])
    #im_shape    = (model.data.shape[1], model.data.shape[2])#(100, 100)#
    #target_size = int(model.target.get_shape()[1])
    pool_len    = 2
    n_features  = 32
    cnn_ksize   = (10,10)
    """
    y1 = model.data + NNlayer.multi_convolution2d(model.data, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (1,          n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  1), \
                                           pool_type = 'None', activate_type = 'ReLU')
    y2 = y1 + NNlayer.multi_convolution2d(y1, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (1,          n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  1), \
                                           pool_type = 'None', activate_type = 'ReLU')
    y3 = y2 + NNlayer.multi_convolution2d(y2, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (1,          n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  1), \
                                           pool_type = 'None', activate_type = 'ReLU')
    """
    
    #out_size = data_size#n_features*data_size//(pool_len**4)
    #y1_4d    = tf.reshape(model.data, [-1,im_shape[0],im_shape[1],1]) #reshape into 4d tensor
    # input size   [-1, im_shape[0],          im_shape[1],         1 ]
    # output size  [-1, im_shape[0],          im_shape[1], n_features ]
    conv1_12 = NNlayer.multi_convolution2d(model.data, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (1,          n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0],          im_shape[1],          n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    pool1    = NNlayer.pool(conv1_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv2_12 = NNlayer.multi_convolution2d(pool1, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    pool2    = NNlayer.pool(conv2_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    conv3_12 = NNlayer.multi_convolution2d(pool2, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features, n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2),      n_features ]
    # output size  [-1, im_shape[0]/(pool_len**3), im_shape[1]/(pool_len**3), n_features ]
    pool3    = NNlayer.pool(conv3_12, pool_size = [1, pool_len, pool_len, 1], \
                            pool_type = 'max_pool')    

    # input size   [-1, im_shape[0]/(pool_len**3), im_shape[1]/(pool_len**3), n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    up4      = NNlayer.deconvolution2d(pool3, cov_ker_size = ( pool_len, pool_len), \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), 2*n_features ]
    merge4   = NNlayer.merge(conv3_12, up4, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), 2*n_features ]
    # output size  [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    conv4_12 = NNlayer.multi_convolution2d(merge4, cov_ker_size = (pool_len, pool_len), n_cnn_layers = 3, \
                                           in_n_features_arr  = (2*n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features,   n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')

    # input size   [-1, im_shape[0]/(pool_len**2), im_shape[1]/(pool_len**2), n_features ]
    # output size  [-1, im_shape[0]/pool_len,      im_shape[1]/pool_len,      n_features ]
    up5      = NNlayer.deconvolution2d(conv4_12, cov_ker_size = ( pool_len, pool_len), \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    merge5   = NNlayer.merge(conv2_12, up5, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, 2*n_features ]
    # output size  [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    conv5_12 = NNlayer.multi_convolution2d(merge5, cov_ker_size = (pool_len, pool_len), n_cnn_layers = 3, \
                                           in_n_features_arr  = (2*n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features,   n_features,  n_features), \
                                           pool_type = 'None', activate_type = 'ReLU')
    # input size   [-1, im_shape[0]/pool_len, im_shape[1]/pool_len, n_features ]
    # output size  [-1, im_shape[0],          im_shape[1],          n_features ]
    up6      = NNlayer.deconvolution2d(conv5_12, cov_ker_size = cnn_ksize, \
                                            in_n_features = n_features, out_n_features = n_features, \
                                            conv_strides = [1, pool_len, pool_len, 1], activate_type = 'ReLU')
    # input size   [-1, im_shape[0], im_shape[1], n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 2*n_features ]
    merge6   = NNlayer.merge(conv1_12, up6, axis = 3, merge_type = 'concat')
    # input size   [-1, im_shape[0], im_shape[1], 2*n_features ]
    # output size  [-1, im_shape[0], im_shape[1], 1 ]
    conv6_12 = NNlayer.multi_convolution2d(merge6, cov_ker_size = cnn_ksize, n_cnn_layers = 3, \
                                           in_n_features_arr  = (2*n_features, n_features,  n_features), \
                                           out_n_features_arr = (n_features,  n_features,   1), \
                                           pool_type = 'None', activate_type = 'sigmoid')
    # input data shape [-1,  data_size/4, 1, cnn_n_feature], output data shape [-1, out_size=n_features*data_size//4]
    #y = tf.reshape(conv6_12, [-1, im_shape[0], im_shape[1]]) #flatten
    # softmax output
    return conv6_12#tf.argmax(conv6_12)

def tf_prediction_func_cnn( model ):
    #if model.arg is None:
    #    model.arg = [1.0, 1.0]
    # get data size
    NNlayer     = tf_layer()
    #data_size   = int(model.data.get_shape()[1])
    #im_shape    = (model.data.shape[1], model.data.shape[2])#(100, 100)#
    #target_size = int(model.target.get_shape()[1])
    pool_len    = 2
    n_features  = 32
    cnn_ksize   = (10,10)
    
    y1 = NNlayer.multi_convolution2d(model.data, cov_ker_size = cnn_ksize, n_cnn_layers = 6, \
                                           in_n_features_arr  = (1,  n_features,  n_features,  n_features,  n_features,  n_features), \
                                           out_n_features_arr = (n_features,  n_features,  n_features,  n_features,  n_features,  1), \
                                           pool_type = 'None', activate_type = 'sigmoid')

    return y1


def dice_coe(prediction, target, axes = (1,2,3), smooth = 0.00001):
    inse = tf.reduce_sum(tf.multiply(prediction, target), axis = axes)
    l    = tf.reduce_sum(tf.multiply(prediction, prediction), axis = axes)
    r    = tf.reduce_sum(tf.multiply(target, target), axis = axes)
    dice = tf.div(2.0 * inse + smooth, l + r + smooth)
    return tf.reduce_mean(dice)

# example of the prediction function, defined using tensorflow lib
def tf_optimize_func( model ):
    #model.arg = 0.5#[0.5, 0.5]
    #loss = tf.reduce_sum(tf.pow(tf.subtract(model.prediction, model.target),2))
    #loss = 1 - dice_coe(model.prediction, model.target)
    loss = -tf.log(dice_coe(model.prediction, model.target))
    optimizer = tf.train.RMSPropOptimizer(1e-4)
    # minimization apply to cross_entropy
    return optimizer.minimize(loss)

# example of the error function, defined using tensorflow lib
def tf_error_func( model ):
    model.arg = 1.0#[1.0, 1.0]
    #training accuracy
    correct_prediction = tf.pow(tf.subtract(model.prediction, model.target),2)**0.5
    return tf.reduce_mean(correct_prediction)/(tf.reduce_mean(model.target)**0.5)

#############################
#code from https://www.kaggle.com/toregil/a-lung-u-net-in-keras/notebook
def get_data( IMAGE_LIB, MASK_LIB, IMG_HEIGHT, IMG_WIDTH ):
    all_images = [x for x in sorted(os.listdir(IMAGE_LIB)) if x[-4:] == '.tif']

    x_data = np.empty((len(all_images), IMG_HEIGHT, IMG_WIDTH), dtype='float32')
    for i, name in enumerate(all_images):
        im = cv2.imread(IMAGE_LIB + name, cv2.IMREAD_UNCHANGED).astype("int16").astype('float32')
        im = cv2.resize(im, dsize=(IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_LANCZOS4)
        im = (im - np.min(im)) / (np.max(im) - np.min(im))
        #im = np.log(im + 1e-4)        
        x_data[i] = im

    y_data = np.empty((len(all_images), IMG_HEIGHT, IMG_WIDTH), dtype='float32')
    for i, name in enumerate(all_images):
        im = cv2.imread(MASK_LIB + name, cv2.IMREAD_UNCHANGED).astype('float32')/255.
        im = cv2.resize(im, dsize=(IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_NEAREST)
        y_data[i] = im
    fig, ax = plt.subplots(1,2, figsize = (8,4))
    ax[0].imshow(x_data[0], cmap='gray')
    ax[1].imshow(y_data[0], cmap='gray')
    plt.show()
    x_data = x_data[:,:,:,np.newaxis]
    y_data = y_data[:,:,:,np.newaxis]
    x_train, x_val, y_train, y_val = train_test_split(x_data, y_data, test_size = 0.1)
    return x_train, x_val, y_train, y_val

def my_generator(x_train, y_train, batch_size):
    SEED = 42
    data_generator = ImageDataGenerator(width_shift_range=0.1*2,
                                        height_shift_range=0.1*2,
                                        rotation_range=90*2,
                                        zoom_range=0.1*2)\
                     .flow(x_train, x_train, batch_size, seed=SEED)
    mask_generator = ImageDataGenerator(width_shift_range=0.1*2,
                                        height_shift_range=0.1*2,
                                        rotation_range=90*2,
                                        zoom_range=0.1*2)\
                     .flow(y_train, y_train, batch_size, seed=SEED)
    while True:
        x_batch, _ = data_generator.next()
        y_batch, _ = mask_generator.next()
        yield x_batch, y_batch

def test1():
    # need to download data from https://www.kaggle.com/kmader/siim-medical-image-analysis-tutorial
    IMAGE_LIB             = '../save_data/heart_data/2d_images/'
    MASK_LIB              = '../save_data/heart_data/2d_masks/'
    IMG_HEIGHT, IMG_WIDTH = 100, 100
    batch_size            = 8
    model                 = tf_wrap.tf_model_top([None, IMG_HEIGHT, IMG_WIDTH,1], [None, IMG_HEIGHT, IMG_WIDTH,1], \
                                                 tf_prediction_func_unet, tf_optimize_func, \
                                                 tf_error_func, arg = 0.5)
    x_train, x_val, y_train, y_val = get_data( IMAGE_LIB, MASK_LIB, IMG_HEIGHT, IMG_WIDTH )
    print('training data size %g; testing data size %g' % (x_train.shape[0],x_val.shape[0]))
    for i in range(2000):
        for _ in range(100):
            image_batch, mask_batch = next(my_generator(x_train, y_train, batch_size))
            #fix, ax = plt.subplots(8,2, figsize=(batch_size,20))
            #for i in range(8):
            #    ax[i,0].imshow(image_batch[i,:,:,0])
            #    ax[i,1].imshow(mask_batch[i,:,:,0])
            #plt.show()
            #image_batch = image_batch + np.random.ranf(1)[0]*np.random.uniform(-0.1,0.1,(image_batch.shape))
            model.train(image_batch, mask_batch)
            model.test(x_val, y_val)
        if 0:#i%2 == 0:
            y_pre = model.prediction(x_val,np.zeros(y_val.shape))
            fig, ax = plt.subplots(8,2, figsize = (8,4))
            for i in range(8):
                ax[i,0].imshow(x_val[i,:,:,0], cmap='gray')
                ax[i,1].imshow(y_pre[i,:,:,0], cmap='gray')
            plt.show()
        if i % 20 == 0:
            model.save('../save_data/test_Unet_on_heart_data')


def test2():
    IMAGE_LIB             = '../save_data/heart_data/2d_images/'
    MASK_LIB              = '../save_data/heart_data/2d_masks/'
    IMG_HEIGHT, IMG_WIDTH = 100, 100
    batch_size            = 8
    model                 = tf_wrap.tf_model_top([None, IMG_HEIGHT, IMG_WIDTH,1], [None, IMG_HEIGHT, IMG_WIDTH,1], \
                                                 tf_prediction_func_unet, tf_optimize_func, \
                                                 tf_error_func, arg = 1.0)
    x_train, x_val, y_train, y_val = get_data( IMAGE_LIB, MASK_LIB, IMG_HEIGHT, IMG_WIDTH )
    model.restore('../save_data/test_Unet_on_heart_data')
    model.test(x_val, y_val)
    y_pre = model.prediction(x_val,np.zeros(y_val.shape))
    fig, ax = plt.subplots(8,2, figsize = (8,4))
    for i in range(8):
        ax[i,0].imshow(x_val[i,:,:,0], cmap='gray')
        ax[i,1].imshow(y_pre[i,:,:,0], cmap='gray')
    plt.show()

#if __name__ == '__main__':
    #test1()
    #test2()
