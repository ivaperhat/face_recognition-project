from unittest import TestCase
import face_recognition
import face_analysis.recognition_functions as fr
import face_analysis.facial_attribute_analysis as fae


class Test(TestCase):
    def test_count_faces(self):
        self.assertEqual(fr.count_faces(fr.get_img_array("beatles.jpg")), 4)
        self.assertEqual(fr.count_faces(fr.get_img_array("miley_cyrus1.jpg")), 1)

    def test_crop_faces(self):
        self.assertEqual(len(fr.crop_faces(face_recognition.load_image_file("beatles.jpg"))), 4)
        self.assertEqual(len(fr.crop_faces(face_recognition.load_image_file("miley_cyrus1.jpg"))), 1)

    def test_face_match(self):
        self.assertEqual(fr.face_match(fr.get_face_encodings(fr.get_img_array("miley_cyrus1.jpg")),
                                       fr.get_face_encodings(fr.get_img_array("miley_cyrus2.jpg"))),
                         True)
        self.assertEqual(fr.face_match(fr.get_face_encodings(fr.get_img_array("miley_cyrus1.jpg")),
                                       fr.get_face_encodings(fr.get_img_array("zendaya1.jpg"))),
                         False)

    def test_face_distance(self):
        self.assertLess(fr.face_distance(fr.get_face_encodings(fr.get_img_array("miley_cyrus1.jpg")),
                                         fr.get_face_encodings(fr.get_img_array("miley_cyrus2.jpg"))), 0.6)
        self.assertGreater(fr.face_distance(fr.get_face_encodings(fr.get_img_array("miley_cyrus1.jpg")),
                                            fr.get_face_encodings(fr.get_img_array("zendaya1.jpg"))), 0.6)

    def test_gender_detection(self):
        self.assertEqual(fae.detect_gender("zendaya1.jpg"), 'f')
        self.assertEqual(fae.detect_gender("leonardo_dicaprio.jpg"), 'm')

    def test_age_detection(self):
        self.assertLess(fae.detect_age("zendaya3.jpg"), 30)
        self.assertGreater(fae.detect_age("leonardo_dicaprio.jpg"), 30)
