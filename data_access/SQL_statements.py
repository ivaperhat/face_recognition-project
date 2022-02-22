# MySQL Statements
FACES_SELECT_ALL = "SELECT * FROM faces"
FACES_SELECT_IMG = "SELECT img_id FROM faces WHERE face_id = %s"
FACES_DELETE_RECORD = "DELETE FROM faces WHERE face_id = %s"
FACES_INSERT = "INSERT INTO faces (name, face_encodings, img_id) VALUES (%s, %s, %s)"
FACES_EXISTS = "SELECT EXISTS(SELECT * FROM faces WHERE face_id = %s)"