from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
import os
from PIL import Image

from absl import app
from absl import flags
from absl import logging


# -------------------------------------
#   Kubeflow Pipeline Component code
# -------------------------------------

def prepare_dataset(pathimg:str, pathimgsubdir:str) -> str:
    """ 
        Create a TFRecord file from jpeg images (containing both the 
        input and target parts), and split it into 2 halves accross the width.     

        Args:
            pathimg (str) : path to the dataset directory
            pathimgsubdir (str) : path to the dataset subdir containing the jpeg files (i.e "train")
            
        Returns:
            String path to the TFRecords file containing the images data
    """
    
    
    # ******************************************************************
    #               HELPER FUNCTIONS TO LOAD AND TRANSFORM 
    #               IMAGES INTO a TENSORFLOW TFRECORD FILE
    #
    #    img_array = load_jpeg(path_to_image, jpeg_file)
    #    img_a , img_b = split_images_array(img_array)
    #
    # *****************************************************************

    def load_jpeg(path_to_image, jpeg_file):
        """ Load a jpeg file and return a numpy array
        Args:
            path_to_image : path to the jpeg files directory
            jpeg_file : jpeg file name
            
        Returns:
            np.array corresponding to the jpeg image
        """
        jpeg_img = Image.open(os.path.join(path_to_image,jpeg_file))
        return np.array(jpeg_img)
    
    def split_images_array(img_array):
        """ Split an image numpy array containing both the input and target parts 
            of the dataset into 2 halves accross the width.     

        Args:
            img_array : np.array corresponding to an image (containing both 
                        the input and target parts concatenated together 
                        accross the width dimension.)

        Returns:
            img_a, img_b : np.array [ height, width, channel ]
        """  
        split_index =  (img_array.shape[1]) // 2
        img_a = img_array[:, :split_index, :]
        img_b = img_array[:, split_index:, :]
        return img_a, img_b

    
    # Helper functions to convert a value to a type compatible with tf.Example
    def _bytes_feature(value):
        """Returns a bytes_list from a string / byte."""
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

    
    # Helper functions to convert a value to a type compatible with tf.Example
    def _int64_feature(value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))  
    

    #------------------------
    #   Prepare Dataset
    #------------------------
    
    # Alias for code readability
    path_to_image =  os.path.join(pathimg, pathimgsubdir)
    print("Loading images from ", path_to_image)
    pathtfrecords = pathimg + "/" + pathimgsubdir +".tfrecords"
    print("Path to TFRecords ", pathtfrecords)
    
 
    # Create a TFRecord writer
    with tf.io.TFRecordWriter(pathtfrecords) as writer:

        # Loop over all the images in the dataset
        for i, jpeg_file in enumerate(os.listdir(path_to_image)):

            # Load jpeg image and convert into a Numpy array
            img_array = load_jpeg(path_to_image, jpeg_file)

            # Split image [height, width, channel] in halves on the width dimension
            img_a, img_b = split_images_array(img_array) 


            # Prepare the features to store in the TFRecord file.
            # We need to store the image width, height and depth to be able             
            # to reconstruct the image when reading the TFRecord file

            file_name = bytes(jpeg_file, 'utf-8')
            height = img_a.shape[0]
            width = img_a.shape[1]
            depth = img_a.shape[2]
            raw_img_a = img_a.tostring()
            raw_img_b = img_b.tostring()

            # Convert the features to the appropriate format
            example = tf.train.Example(features=tf.train.Features(feature={
                'jpeg_file': _bytes_feature(file_name), 
                'height': _int64_feature(height),
                'width': _int64_feature(width),
                'depth' : _int64_feature(depth),
                'raw_img_a': _bytes_feature(raw_img_a),
                'raw_img_b': _bytes_feature(raw_img_b)
            }))

             # Append the features correponding to the current image into the TFRecords file
            writer.write(example.SerializeToString())

            # Add monitoring info
            if (i % 100 == 0):
                print("[INFO] {} images processed into the TFRecord file".format(i))

        print("\n[INFO] Processing is finised: {} jpeg images processed into {}\n".format(i, pathtfrecords))
    
    
    # Output of the Kubeflow Pipeline Component
    with open('/output.txt', 'w') as f:
        f.write(pathtfrecords)
    
    # Return the path to the TFRecord file     
    return pathtfrecords    
 

# ---------
#   Main
# ---------

flags.DEFINE_string('pathimg', None, 'Path to the dataset directory')
flags.DEFINE_string('pathimgsubdir', None, 'Path to the dataset subdir containing the jpeg files (i.e "train")')

FLAGS = flags.FLAGS


def main(argv):
    del argv  # Unused.
    
    prepare_dataset(FLAGS.pathimg , FLAGS.pathimgsubdir)


if __name__ == '__main__':
    app.run(main)

    
    
