# Overview
In this lab you'll learn how to extract data from a local relational database, transform the content into parquet format and store on S3 using Glue. Finally you will use AWS QuickSight to visualise the data to gain insight.

# Setup
<details>
<summary><strong>Generate a KeyPair</strong></summary><p>

**Generate a Keypair**

**Note** If you are using windows 7 or earlier you will need to download and install Putty and Puttygen from [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html).

1. From the AWS console search for EC2 in the search box and select the service.
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/EC2_console.png">
    </p>

1. From the left-hand menu select **Key Pairs**.
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/Key_Pair_menu.png">
    </p>

1. Click the **Create Key Pair** button and enter a name for the *glue-lab* for the demo. This will download the private key to your local machine.
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/Create_key_pair.png">
    </p>

**Note** If you are running windows you need to follow [these instructions](https://aws.amazon.com/premiumsupport/knowledge-center/convert-pem-file-into-ppk/) to convert the key to putty.

</details>

<details>
<summary><strong>Deploy a database to mimic on-premesis</strong></summary><p>

To demonstrate the data being held in a different location we'll build our fake database in the Ireland region using CloudFormation.

Click the button below to deploy the stack.

| AWS Region | Short name | | 
| -- | -- | -- |
| EU West (Ireland) | eu-west-1 | <a href="https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=fakedb&templateURL=https://s3-eu-west-1.amazonaws.com/aws-shared-demo-cf-templates/fake-database/master_template.yaml" target="_blank"><img src="images/cloudformation-launch-stack.png"></a> |

1. On the next page click **Next**
1. Enter the **KeyPairName** name created above *glue-lab* and click **Next**
1. click **Next**
1. Check the last two boxes:
    - *I acknowledge that AWS CloudFormation might create IAM resources with custom names.*
    - *I acknowledge that AWS CloudFormation might require the following capability: CAPABILITY_AUTO_EXPAND*
    <p align="left">
      <img width="500" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/Cloudformation-approval.png">
    </p>
1. Click **Create Stack**
1. Wait for the stack to return **CREATION_COMPLETE** and then click the **Outputs** tab and record the database server IP address.
    <p align="left">
      <img width="500" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/cloudformation-output.png">
    </p>

**Note:** In reality the IP would be a private address access via a VPN on Direct Connect.

</details>

# Data import

## Configuring a Glue Connection

<details>
<summary><strong>Setup a Nat Gateway</strong></summary><p>

Glue can only connect to the internet via a Nat Gateway for security. In reality you would be more likely to be routing from a private subnet to a database on-premesis via a VPN. However for this lab we'll configure a VPN Gateway to allow us to connect to the database we deployed with internet access in the previous step.

1. In the top right of the AWS console choose **Ireland** and then select **London** from the dropdown.
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/select-region.png">
    </p>
**Note:** you can ignore the errors about the stack not existing.
1. Click on the **Services** dropdown in the top right and select the service **VPC**
1. Click on **NAT Gateways** on the left-hand menu
1. Click **Subnet** and selct any subnet
1. Click **Create New EIP**
1. Click **Create a NAT Gateway**, **Close**
1. Click on **Subnets** on the left-hand menu
1. Click **Create Subnet**
1. Enter *Glue Private Subnet* for the **Name Tag**
1. Enter and appropriate CIDR block in the **IPv4 CIDR Block**
1. Click **Create**
1. Click on **Route Tables** on the left-hand menu
1. Click **Create Route Table**
1. Enter *Glue private route* as the **Name Tag**
1. Click **Create**, **Close**
1. Check the route table you just created and select **Subnet Associations** tab at the bottom
1. Click **Edit subnet associations**
1. Place a check next to the *Glue Private Subnet*
1. Click **Save**
1. Click the **Routes** tab
1. Click **edit routes**
1. Click **Add Route**
1. Enter *0.0.0.0/0* for the **Destination** 
1. For the **Target** select the *NAT Gateway* you created earlier
1. Click **Save Routes**, **Close**

</details>

<details>
<summary><strong>Setup an S3 endpoint</strong></summary><p>

In order to securely transfer data from the on-premesis database to S3 Glue uses an S3 endpoint which allows for data transfer over the AWS backbone once the data reaches your AWS VPC.

In order to demonstrate the data being consumed remotely to the VPC like it would be on-premesis we'll use the London region (eu-west-2).

1. Click on **endpoints** on the left-hand menu
1. Click on **Create Endpoint**
1. Place a check next to **com.amazonaws.eu-west-2.s3** and place a check in the routetable you created in the previous step starting **rtb-**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/s3-endpoint.png">
    </p>
1. Click **Create Endpoint**
1. Click **Close**

</details>

<details>
<summary><strong>Create a security group for Glue</strong></summary><p>

Glue requires access both out of the VPC to connect to the database but also to the glue service and S3.

1. From the left-hand menu click **Security Groups**
1. Clock **Create security group**
1. For **Security Group Name** enter *on-prem-glue-demo*
1. For **Description** enter *Glue demo*
1. For **VPC** select the *Default VPC*
1. Click **Create**, then **Close**
1. Select the security group you just created and copy the **Group Id** to a text doc
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/sg-id.png">
    </p>
1. Select **Actions** --> **Edit inbound rules**
1. Click **Add Rule** and enter **All TCP** for the **Type** 
1. Enter the **Group Id** recorded above in the field **CIDR, IP, Security Group or Prefix List**
1. Click **Save rules**, **Close**

</details>

<details>
<summary><strong>Setup a Glue IAM Role</strong></summary><p>

In order for Glue to run we need to give the service the required permissions to manage infrastructure on our behalf.

1. Click on the **Services** dropdown in the top right and select the service **IAM**
1. On the left-hand menu select **Roles**
1. Click **Create Role**
1. Under **Choose the service that will use this role** select **Glue**
1. Click **Next: Permissions**
1. Search for **Glue** and place a check next to **AWSGlueServiceRole**
1. Next search for **s3** and place a check next to **AmazonS3FullAccess**
1. Click **Next: Tags**
1. Click **Next: Review**
1. Enter *glue-demo-role* for the **Role Name**
1. Click **Create Role**

</details>

<details>
<summary><strong>Setup a Glue Connection</strong></summary><p>

In order to transfer the data from the on-premesis database we need to setup a glue connection with the database connection details.

1. Click on the **Services** dropdown in the top right and select the service **AWS Glue**
1. On the left-hand menu select **Connections** and click **Add Connection**
1. Type the **Name** *on-prem-database*
1. Select **JDBC** as the **Connection Type** and click **Next**
1. For the JDBC connection enter the following string replacing the **IP_ADDRESS** with the IP address recorded from the cloudformation stack output,
    ```
    jdbc:mysql://IP_ADDRESS:3306/employees
    ```
    e.g.
    ```
    jdbc:mysql://52.212.137.195:3306/employees
    ```
1. Enter **Username**, *dbuser* and **Password**, *password12345*
1. Select your **VPC** 
1. Select any **Subnet** 
1. Select the **Security Group** with the name **on-prem-glue-demo** and choose **Next**
1. Click **Finish**

</details>

<summary><strong>Test the Glue Connection</strong></summary><p>

1. Click **Test Connection**
1. Select the role **glue-demo-role** created previously
1. Click **Test Connection**
1. This should result in success (it may take a few minutes)
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-success.png">
    </p>

</details>

## Configure Glue ETL

Next we'll configure Glue to perform ETL on the data to convert it to Parquet and store it on S3.

<details>
<summary><strong>Create an S3 bucket</strong></summary><p>

In order to store the data extracted from the on-premesis database we'll create an S3 bucket.

1. Click on the **Services** dropdown in the top right and select the service **S3**
1. Click **Create Bucket**
1. Enter a unique name for the bucket e.g. *firstname-lastname-glue-demo*
1. Click **Create**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/s3-setup.png">
    </p>

</details>

<details>
<summary><strong>Setup a Glue Connection</strong></summary><p>

1. On the left-hand menu select **Jobs**
1. Click **Add Job**
1. Enter *Glue-demo-job* for the **Name**
1. Select the **Role** *glue-demo-role*
1. Under **This job runs** select **A new script to be authored by you**
1. Click **Next**
1. Under **All Connections** click **Select** next to **on-prem-database**
1. Click **Save job and edit script**
1. Paste in the script below
    ```
    import sys
    import boto3
    import json
    from awsglue.transforms import *
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext
    from awsglue.context import GlueContext
    from awsglue.dynamicframe import DynamicFrame
    from awsglue.job import Job
    
    s3_bucket_name = "s3://cjl-glue-mysql-database-sample"
    db_url = 'jdbc:mysql://52.30.96.60:3306/employees'
    
    ## @params: [JOB_NAME]
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    db_username = 'dbuser'
    db_password = 'password12345'
    
    #Table current_dept_emp
    table_name = 'current_dept_emp'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("dept_no", "string", "dept_no", "string"), ("from_date", "date", "from_date", "date"), ("to_date", "date", "to_date", "date"), ("emp_no", "int", "emp_no", "int")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table departments
    table_name = 'departments'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("dept_no", "string", "dept_no", "string"), ("dept_name", "string", "dept_name", "string")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table dept_emp
    table_name = 'dept_emp'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("dept_no", "string", "dept_no", "string"), ("dept_name", "string", "dept_name", "string")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table dept_emp_latest_date
    table_name = 'dept_emp_latest_date'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("from_date", "date", "from_date", "date"), ("to_date", "date", "to_date", "date"), ("emp_no", "int", "emp_no", "int")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table dept_manager
    table_name = 'dept_manager'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("dept_no", "string", "dept_no", "string"), ("from_date", "date", "from_date", "date"), ("to_date", "date", "to_date", "date"), ("emp_no", "int", "emp_no", "int")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table employees
    table_name = 'employees'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("gender", "string", "gender", "string"), ("emp_no", "int", "emp_no", "int"), ("birth_date", "date", "birth_date", "date"), ("last_name", "string", "last_name", "string"), ("hire_date", "date", "hire_date", "date"), ("first_name", "string", "first_name", "string")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table salaries
    table_name = 'salaries'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("from_date", "date", "from_date", "date"), ("to_date", "date", "to_date", "date"), ("emp_no", "int", "emp_no", "int"), ("salary", "int", "salary", "int")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    #Table titles
    table_name = 'titles'
    s3_output = s3_bucket_name + "/" + table_name
    
    # Connecting to the source
    df = glueContext.read.format("jdbc").option("url", db_url).option("dbtable", table_name).option("user", db_username).option("password", db_password).option("driver","com.mysql.jdbc.Driver").load()
    df.printSchema()
    print df.count()
    datasource0 = DynamicFrame.fromDF(df, glueContext, "datasource0")
    applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("from_date", "date", "from_date", "date"), ("to_date", "date", "to_date", "date"), ("emp_no", "int", "emp_no", "int"), ("title", "string", "title", "string")], transformation_ctx = "applymapping1")
    resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
    dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
    datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": s3_bucket_name + "/" + table_name}, format = "parquet", transformation_ctx = "datasink4")
    
    job.commit()
    ```
1. Edit lines 11 and 12 so the vairables **s3_bucket_name** and **db_url** reflect the correct values created above.
1. Click **Save**, **Run Job** and then confirm by clicking **Run Job**

</details>
