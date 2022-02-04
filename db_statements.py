# MySQL Statements
faces_select = "SELECT * FROM faces"
faces_delete_ID = "DELETE FROM faces WHERE face_id = %s"
faces_insert_NAME_ENCODINGS = "INSERT INTO faces (name, face_encodings) VALUES (%s, %s)"
faces_exists_ID = "SELECT EXISTS(SELECT * FROM faces WHERE face_id = %s)"
