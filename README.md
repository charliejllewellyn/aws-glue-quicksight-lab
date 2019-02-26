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
<summary><strong>Deploy a database to mimic on-premises</strong></summary><p>

To demonstrate the data being held in a different location we'll build our fake database in the Ireland region using CloudFormation.

Click the button below to deploy the stack.

| AWS Region | Short name | | 
| -- | -- | -- |
| EU West (London) | eu-west-2 | <a href="https://console.aws.amazon.com/cloudformation/home?region=eu-west-2#/stacks/new?stackName=fakedb&templateURL=https://s3-eu-west-1.amazonaws.com/aws-shared-demo-cf-templates/fake-database/master_template.yaml" target="_blank"><img src="images/cloudformation-launch-stack.png"></a> |

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

## Prepare your VPC for Glue

If you are time constrained you can stage the next **4** steps by running the following CloudFormation template. If you do this move to **Configuring a Glue Connection**

| AWS Region | Short name | |
| -- | -- | -- |
| EU West (Ireland) | eu-west-1 | <a href="https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=glue-demo&templateURL=https://s3-eu-west-1.amazonaws.com/aws-shared-demo-cf-templates/glue_demo/master_template.yaml" target="_blank"><img src="images/cloudformation-launch-stack.png"></a> |

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
<summary><strong>Setup a Nat Gateway</strong></summary><p>

Glue can only connect to the internet via a Nat Gateway for security. In reality you would be more likely to be routing from a private subnet to a database on-premises via a VPN. However for this lab we'll configure a VPN Gateway to allow us to connect to the database we deployed with internet access in the previous step.

1. In the top right of the AWS console choose **London** and then select **Ireland** from the dropdown.
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

## Configuring a Glue Connection

<details>
<summary><strong>Setup a Glue Connection</strong></summary><p>

In order to transfer the data from the on-premises database we need to setup a glue connection with the database connection details.

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
1. Select your **VPC** created earlier, if you used the CloudFormation template it will be labeled *glue-demo*
1. Select any private **Subnet**, e.g. *glue-demo-private-a*
1. Select the **Security Group** with the name **on-prem-glue-demo** and choose **Next**
1. Click **Finish**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-connection.png">
    </p>

</details>

<details>
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

In order to store the data extracted from the on-premises database we'll create an S3 bucket.

1. Click on the **Services** dropdown in the top right and select the service **S3**
1. Click **Create Bucket**
1. Enter a unique name for the bucket e.g. *firstname-lastname-glue-demo*
1. Click **Create**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/s3-setup.png">
    </p>

</details>

<details>
<summary><strong>Create a Glue Job</strong></summary><p>

1. Click on the **Services** dropdown in the top right and select the service **AWS Glue**
1. On the left-hand menu select **Jobs**
1. Click **Add Job**
1. Enter *Glue-demo-job* for the **Name**
1. Select the **Role** *glue-demo-role*
1. Under **This job runs** select **A new script to be authored by you**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-job-connection.png">
    </p>
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

**Note:** you can move onto create the crawler whilst the job is runnning, **but** make sure the job is complete before you run the crawler

</details>

<details>
<summary><strong>Create a Glue Crawler</strong></summary><p>

We use a glue crawler to query the data from the database on S3 and create a schema so we can start to interogate the information.

1. From the left-hand menu select **Crawlers**
1. Select **Add Crawler**
1. For **Name** enter *on-prem-database*, click **Next**
1. In the **Include path** enter the bucket name from earlier, e.g. *s3://firstname-lastname-glue-demo"
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-crawler-datasource.png">
    </p>
1. Click **Next**, **Next**
1. Select **Choose an existing IAM role** and select the role **glue-demo-role**
1. Click **Next**, **Next**
1. Click **Add database** and enter the name *on-prem-employee-database*, click **Create**
1. Click **Next**
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-crawler-details.png">
    </p>
1. Click **Finish**
1. Place a check next to your crawler and click **Run Crawler**
1. Wait for the crawler to run and then choose **Tables** from the left-hand menu
1. This should show you the tables for your newly extracted data.
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/glue-tables.png">
    </p>

</details>

# Data Visualisation

Once the data is available in S3 we can start to query and visualisae the data. In this section we'll be using AWS QuickSight but other products can be integrated like Tableau, or qlik.

<details>
<summary><strong>Allow QuickSight access to your data</strong></summary><p>

1. Click on the **Services** dropdown in the top right and select the service **QuickSight**
1. In the top right-hand corner click **Admin**, **Manage QuickSight**
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-perms.png">
    </p>
1. In the left-hand menu click **Account Settings**
1. Click **Manage QuickSight permissions**
1. Select **Choose S3 buckets**
1. Place a check next to the bucket you created earlier
1. Click **Select Buckets** and click **Update**


</details>

<details>
<summary><strong>Prepare the datasource</strong></summary><p>

1. In the top right-hand corner click **N. Virgina** and select **EU (Ireland)**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-region.png">
    </p>
1. On the left hand page click **New Analysis**
1. Click **New dataset**
1. Select **Athena** and enter *glue-demo* for the **Data source Name**
1. Click **Create Data Source**
1. Select **on-prem-employee-database**
1. Select **employees** as the **Table**
1. Click **edit preview data**
1. Click **add data**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-add-data.png">
    </p>
1. Select **Salaires** as the table and click **Select**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-add-table.png">
    </p>
1. Click on the two circles and under the **Join Clauses** select **emp_no** for both **employees** and **salaries**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-join.png">
    </p>
1. Click **Apply**
1. Click **add data**
1. Select **dept_manager** as the table, click select
1. Click on the two circles and under the **Join Clauses** select **emp_no** for both **employees** and **dept_manager**
1. Click **Apply**
1. Click **add data**
1. Select **deptartments** as the table, click select
1. This time drag the **departments** box over the **dept_manager** box and release when it turns green.
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-new-join.png">
    </p>
1. Click on the two circles and under the **Join Clauses** select **dept_no** for both **employees** and **dept_manager**
1. Click **Apply**
1. At the top click **Save & Visualise**

</details>

</details>

<details>
<summary><strong>Build some visualisations</strong></summary><p>

1. Choose your visulisation type, in this case select the **bar chart** icon
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-new-join.png">
    </p>
1. From teh left-hand menu select **gender[employees]**
1. Click the bar saying **Field Wells** at the top
1. Drag **Salaries** into the **Value** box and then click to select **Aggregate** as **Average**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-vis-1.png">
    </p>
1. In the top left you select **Add**, **Add Visual**
1. This time select **Horizontal bar chart**
    <p align="left">
      <img width="200" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/qs-hor-bar.png">
    </p>
1. Select **dept_name** from the left-hand menu
1. Now drag **salary** to the **Value** box in the top bar
1. Feel free to continue building your own visulaisations to explore the data

</details>

# Summary
During this lab you extracted data from an "on-premises" database, converted it to Parquet and stored the output to S3. You then used a combination of Athena and QuickSight to query and visualise the data to start exploiting it.

This is a simple lab but could easily be expanded to pull data from multiple sources to start corelating it to gain deeper insight.
