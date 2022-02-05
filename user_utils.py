import psycopg2
from psycopg2 import Error

user = 'shikhar_srivastava'
password = 'b@m*n%Z-njdv*M73DLeP2j29QkNd=qpW?bMTngwa'
endpoint = 'datawarehouse-production.cpbbk0zu5qod.eu-central-1.redshift.amazonaws.com'
port = 5439
database = 'dev'



def create_conn():
    # config = kwargs['config']
    try:
        con=psycopg2.connect(user=user,
                                  password=password,
                                  host=endpoint,
                                  port=port,
                                  database=database)
        return con
    except Exception as err:
        print(err)



bo_login_id = 'shikhar@grover.com'
bo_login_pwd = 'USC@28081989'