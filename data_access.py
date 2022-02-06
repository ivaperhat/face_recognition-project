# Clever Cloud MySQL Database
HOSTNAME = "b97ulbrnkhrhixtxfcii-mysql.services.clever-cloud.com"
USER = "u52rwvwh0rmc0i50"
PASSWORD = "33iXkQ0rI0nyTR1EQbu0"
DATABASE = "b97ulbrnkhrhixtxfcii"

# AWS S3 Bucket
ACCESS_KEY = 'AKIATUBPYMZCWOIYMNGA'
SECRET_ACCESS_KEY = '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'

# MySQL Statements
FACES_SELECT_ALL = "SELECT * FROM faces"
FACES_SELECT_IMG = "SELECT img_id FROM faces WHERE face_id = %s"
FACES_DELETE_RECORD = "DELETE FROM faces WHERE face_id = %s"
FACES_INSERT = "INSERT INTO faces (name, face_encodings, img_id) VALUES (%s, %s, %s)"
FACES_EXISTS = "SELECT EXISTS(SELECT * FROM faces WHERE face_id = %s)"
