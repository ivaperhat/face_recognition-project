import MySQLdb
import boto3

# AWS MySQL Database
HOSTNAME = 'faces-db.crbtdjvdgyor.eu-central-1.rds.amazonaws.com'
USER = 'admin'
PASSWORD = 'adminpassword123'
DATABASE = 'faces'

# AWS S3 Bucket
ACCESS_KEY = 'AKIATUBPYMZCWOIYMNGA'
SECRET_ACCESS_KEY = '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'

# Connect to S3 Bucket
client = boto3.client('s3',
                      aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_ACCESS_KEY)

# Connect to MySQL Database
connection = MySQLdb.connect(host=HOSTNAME,
                             user=USER,
                             passwd=PASSWORD,
                             db=DATABASE)

# MySQL Statements
FACES_SELECT_ALL = "SELECT * FROM faces"
FACES_SELECT_IMG = "SELECT img_id FROM faces WHERE face_id = %s"
FACES_DELETE_RECORD = "DELETE FROM faces WHERE face_id = %s"
FACES_INSERT = "INSERT INTO faces (name, face_encodings, img_id) VALUES (%s, %s, %s)"
FACES_EXISTS = "SELECT EXISTS(SELECT * FROM faces WHERE face_id = %s)"

# Bucket info
BUCKET_FOLDER = "faces/"
BUCKET_NAME = "faces-db-bucket"
