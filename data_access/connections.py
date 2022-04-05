import MySQLdb
import boto3

# AWS MySQL Database
HOSTNAME = 'faces-mysql.cm8fsfd9dzsf.us-east-1.rds.amazonaws.com'
USER = 'admin'
PASSWORD = 'adminpassword123'
DATABASE = 'faces'

# AWS S3 Bucket
ACCESS_KEY = 'AKIA2SHH76PBB7YOQ7TM'
SECRET_ACCESS_KEY = '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'
BUCKET_FOLDER = "faces/"
BUCKET_NAME = "faces-db-bucket"

# Connect to S3 Bucket
client = boto3.client('s3',
                      aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_ACCESS_KEY)


def mysql_connection():
    HOSTNAME = 'faces-mysql.cm8fsfd9dzsf.us-east-1.rds.amazonaws.com'
    USER = 'admin'
    PASSWORD = 'adminpassword123'
    DATABASE = 'faces'

    connection = MySQLdb.connect(host=HOSTNAME,
                                 user=USER,
                                 passwd=PASSWORD,
                                 db=DATABASE)

    return connection
