from __future__ import print_function # Python 2/3 compatibility
import json
import boto3
import pymysql
import cms_config
import MySqlUtil
import time
import uuid
import CmsUtil

db_username = cms_config.db_username
db_password = cms_config.db_password
db_name = cms_config.db_name
db_endpoint = cms_config.db_endpoint
aws_region = cms_config.region 

G_STR_PROJECT_PREFIX = "CMS"
G_STR_DELIM_UNDERSCORE = "_"
G_STR_SNS = "SNS"
G_STR_SQS = "SQS"
G_STR_SERVICE_TOPIC = "SERVICE"
G_STR_REGION_EAST = 'us-east-1'
G_STR_CREATE_SERVICES_SUBSCRIPTION_LAMBDA = "CMS_createServicesSubscription"
G_STR_NOTIFY_INSIGHT_LAMBDA = 'CMS_notifyInsight'
G_STR_STATE_STORE_LAMBDA = "CMS_stateStoreLambda"
algo_name = ""

def get_lambda_arn(lambda_name, region_name_str):
    lambda_client = boto3.client('lambda', region_name=region_name_str)
    
    print(region_name_str)
    resp = lambda_client.get_function_configuration(FunctionName=lambda_name)

    if 'FunctionArn' in resp:
        print(resp['FunctionArn'])
        return resp['FunctionArn']
    else:
        return ""
  
def is_statement_exists(function_name, statement_id):
    try:
        print('in d  statement_id')
        lambda_client = boto3.client('lambda', region_name =cms_config.region)
        
        response = lambda_client.get_policy(FunctionName = function_name)
        
        policy = response['Policy']
        policy_dict = json.loads(policy)
        
        lambda_statement = policy_dict['Statement']
        print(lambda_statement)
        for statement in lambda_statement:
            if statement_id == statement['Sid']:
                if statement['Effect'] == 'Allow' :
                    return True
                else:
                    # remove permission from Lambda first and return False.
                    lambda_client.remove_permission(
                        FunctionName = function_name,
                        StatementId = statement_id)
                    return False
        # statement not found in policy, return False.
        return False
        
    except:
            return False
            
def create_sns_topic(sns, Id):
    sns_topic_name = G_STR_PROJECT_PREFIX + G_STR_DELIM_UNDERSCORE + G_STR_SNS + G_STR_DELIM_UNDERSCORE + str(Id)
    print("Creating opic : " + sns_topic_name)

    # No need to check if topic is already created or not, it will return topic ARN f already created.

    response = sns.create_topic(Name=sns_topic_name)
    
    return response['TopicArn']
    
def VerifySession(connection, cursor, ownerName, ownerPassword):
    print('in verify session')
    if ownerName == "*":
        return True
    print('something')
    tabNameId = {"TableName":cms_config.core_user_table, "IdName":"USER_ID"}
    password_queried = ''

    MySqlUtil.SelectFromColumnQuery(connection, cursor, tabNameId, "PASSWORD", (ownerName))
    if cursor.rowcount > 0:
        password_queried = cursor.fetchone()[0]

    return password_queried == ownerPassword
            
def GenerateAlgoClientId():
    return str(uuid.uuid1())

def subscribeStateUpdateQueue(connection, cursor, sns_arn):
    print('subscribing the queue to new sns')
    MySqlUtil.SelectAll(connection, cursor, cms_config.state_update_queue_table)
    if cursor.rowcount > 0:
        records = cursor.fetchall()
        for row in records:
            queue_url = row[1]

    #get queue arn 
    sqs_client = boto3.client('sqs', region_name = cms_config.region)
    sns_client = boto3.client('sns', region_name = cms_config.region)
    response = sqs_client.get_queue_attributes(QueueUrl = queue_url, AttributeNames = ['QueueArn'])
    queue_arn = response['Attributes']['QueueArn']
    response = sns_client.subscribe(TopicArn = sns_arn, Protocol = 'sqs', Endpoint = queue_arn)
    
    sub_arn = response.get('SubscriptionArn', None)
    if sub_arn is not None:
        print('queue is subscribed')
    print('----------------------------------------')

def subscribeModelOutputQueue(connection, cursor, sns_arn):
    print('subscribing the queue to new sns')
    MySqlUtil.SelectAll(connection, cursor, cms_config.model_output_queue_table)
    if cursor.rowcount > 0:
        records = cursor.fetchall()
        for row in records:
            queue_url = row[1]

    #get queue arn 
    sqs_client = boto3.client('sqs', region_name = cms_config.region)
    sns_client = boto3.client('sns', region_name = cms_config.region)
    response = sqs_client.get_queue_attributes(QueueUrl = queue_url, AttributeNames = ['QueueArn'])
    queue_arn = response['Attributes']['QueueArn']
    response = sns_client.subscribe(TopicArn = sns_arn, Protocol = 'sqs', Endpoint = queue_arn)
    
    sub_arn = response.get('SubscriptionArn', None)
    if sub_arn is not None:
        print('queue is subscribed')

def subscribeLambdaAndClientSqs(targetInstanceId):
    #invoke CMS_createServicesSubscription lambda asynchronously
    lambda_client = boto3.client('lambda', region_name = cms_config.region)
    
    inputSubscribeSnsLambda = {}
    inputSubscribeSnsLambda.update({"subscription_type":"SnsLambda",
                                 "caller_id":targetInstanceId,
                                 "service_id":targetInstanceId})

    lambda_client.invoke(FunctionName = G_STR_CREATE_SERVICES_SUBSCRIPTION_LAMBDA,
                    InvocationType = 'Event',
                    Payload = json.dumps(inputSubscribeSnsLambda)
                    )

def createMMServiceTable(instanceId):
    print('create table for MMService table')
    mm_service_table_name = cms_config.mm_service_tablename_key + str(instanceId)
    sqlQuery = "CREATE TABLE IF NOT EXISTS "+ mm_service_table_name 
    #connect to database of MMService
    conn = MySqlUtil.ConnectDatabase(hostEndPoint = db_endpoint, databaseName=cms_config.mm_service_database,
        userName = db_username, passWord=db_password)
    cursor = conn.cursor()
    sqlQuery = sqlQuery + "(KeyId VARCHAR(255), LastTimestamp INT, ModelOutput JSON, PRIMARY KEY (KeyId))"
    MySqlUtil.ExecuteSqlQuery(conn, cursor, sqlQuery)

def NotifyInsight(instanceId, instanceType, ownerName):
    #invoke CMS_createServicesSubscription lambda asynchronously
    lambda_client = boto3.client(service_name = 'lambda', region_name = cms_config.region)
    
    notifyInsightLambda = {}
    notifyInsightLambda.update({"instance_id":instanceId,
                                 "instance_type":instanceType,
                                 "owner_name":ownerName})

    lambda_client.invoke(FunctionName = G_STR_NOTIFY_INSIGHT_LAMBDA,
                    InvocationType = 'Event',
                    Payload = json.dumps(notifyInsightLambda)
                    )
          
def lambda_handler(event, context):
    # TODO implement
    instance_name   = event.get('instance_name', None)
    instance_version= event.get('instance_version', None)
    instance_type   = int(event.get('instance_type', None))
    instance_param  = event.get('instance_param', None) #json dictionary
    owner_name      = event.get('owner_name', None)
    owner_password  = event.get('password', None)
    car_instance_id = event.get('car_instance_id', None)
    host_address    = event.get('host_address', None)
    port1           = event.get('port1', None)
    port2           = 0

    if instance_type == (CmsUtil.InstanceTypes.eIT_CAR.value):
        car_instance_id = 0
     
    secondsFromEpoch = time.time()
    print(secondsFromEpoch)
    t1 = time.time()
    #connection to rds database
    rds_client = boto3.client('rds')
    if((rds_client.describe_db_instances(DBInstanceIdentifier=cms_config.rds_database))['DBInstances'][0]['DBInstanceStatus']!='available'):
        rds_client.start_db_instance(DBInstanceIdentifier=cms_config.rds_database)
        
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=cms_config.rds_database)
    try:
        conn = MySqlUtil.ConnectDatabase(hostEndPoint = db_endpoint, databaseName=cms_config.status_database,
        userName = db_username, passWord=db_password)
        cursor = conn.cursor()
        
        #verify sessionid for client
        res = VerifySession(conn, cursor, owner_name, owner_password)
        print('result from verifying session is: {}'.format(res))
        
        if res:
            #generate instance id
            #check if owner  has already a session id
            tabIdName = {"TableName":cms_config.session_status_table, "IdName":"ACCOUNT_NAME"}
            MySqlUtil.SelectFromColumnQuery(conn, cursor,tabIdName, "SESSION_ID", (owner_name,))
            if cursor.rowcount == 0:
                session_id = CmsUtil.GenerateUUID()
            else:
                session_id = cursor.fetchone()[0]

            print("session id is: {}".format(session_id))
            instance_id = CmsUtil.genInstanceId(conn, cursor)
            sns_arn = CmsUtil.create_sns_topic(instance_id)
            sqs_url = CmsUtil.create_sqs_queue(instance_id)
    
            
            
            market_data_srv_id = 0
            modeling_service_id = 0
            
            #update the session status table
            insertDict = {"INSTANCE_ID":instance_id, 
                          "TIME_CREATED":secondsFromEpoch, "TIME_UPDATED":secondsFromEpoch, "STATUS":0}
            if instance_type != (CmsUtil.InstanceTypes.eIT_DeepRInsight.value):
                insertDict.update({"ACCOUNT_NAME":owner_name, "SESSION_ID":session_id})

            MySqlUtil.InsertQuery(conn, cursor, cms_config.session_status_table, insertDict)
            
            print(instance_id)
            print(sns_arn)
            print(sqs_url)
 
            inputDict = {"INSTANCE_ID":instance_id, "INSTANCE_TYPE":instance_type,"VERSION":instance_version,
                         "TOPIC_ARN":sns_arn, "QUEUE_URL":sqs_url, "INSTANCE_NAME":instance_name,
                         "TIME_CREATED":secondsFromEpoch,"TIME_UPDATED":secondsFromEpoch,
                         "STATUS":CmsUtil.StatusTypes.eST_Registered.value,
                         "DELETE_STATUS":CmsUtil.DeleteStatus.eDS_NotDeleted.value} 
            
            if host_address is not None:
                inputDict.update({"HOST_ADDRESS":host_address})
            if port1 is not None:
                inputDict.update({"PORT1":port1})
            if port2 is not None:
                inputDict.update({"PORT2":port2})
            if car_instance_id is not None:
                inputDict.update({"CAR_INSTANCE_ID":car_instance_id})
            if session_id is not None:
                inputDict.update({"SESSION_ID":session_id})
            if instance_param is not None:
                inputDict.update({"INSTANCE_PARAMETERS":instance_param})
            
            returnDict = dict()
            MySqlUtil.InsertQuery(conn, cursor, cms_config.instance_status_table,inputDict)
            if instance_type == CmsUtil.InstanceTypes.eIT_ModelingServer.value:
                sns_client = boto3.client('sns', region_name = G_STR_REGION_EAST)
                sns_topic_name = G_STR_PROJECT_PREFIX + G_STR_DELIM_UNDERSCORE + G_STR_SNS + \
                    G_STR_DELIM_UNDERSCORE + G_STR_SERVICE_TOPIC + G_STR_DELIM_UNDERSCORE + str(instance_id)
                print("Creating SNS topic : " + sns_topic_name)
                response = sns_client.create_topic(Name=sns_topic_name)
                sns_arn2 = response['TopicArn']
                #update the value in instance status table
                tabnameidname = {"TableName":cms_config.instance_status_table, "IdName":"INSTANCE_ID"}
                input_dict = {"INSTANCE_ID":instance_id, "SERVICE_TOPIC":sns_arn2}
                MySqlUtil.UpdateQuery(conn, cursor, tabnameidname, input_dict)
                returnDict.update({"topic_arn2":sns_arn2})

                #create table in MMService
                createMMServiceTable(instance_id)
                subscribeModelOutputQueue(conn, cursor, sns_arn2)


            #subscribeLambdaAndClientSqs(instance_id)
            subscribeStateUpdateQueue(conn, cursor, sns_arn)
            NotifyInsight(instance_id, instance_type, owner_name)
            MySqlUtil.CloseConnection(conn)
        
            returnDict.update({"instance_id":instance_id, "topic_arn":sns_arn,
                "queue_url":sqs_url, "session_id":session_id})
            if instance_type == CmsUtil.InstanceTypes.eIT_Algorithm.value:
                returnDict.update({"market_data_service_id":market_data_srv_id,
                 "modeling_service_id":modeling_service_id})
            elif instance_type == CmsUtil.InstanceTypes.eIT_ModelingServer.value:
                returnDict.update({"market_data_service_id":market_data_srv_id})
            t2 = time.time()
            print('execution time is: ', t2-t1)
            return {
                'status': 0,
                'message': json.dumps(returnDict)
            }
          
    except:
        return {
            'status':1,
            'message':json.dumps({"error":"function call failed"})
        }






