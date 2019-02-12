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
1. Click **Create Stack**
1. Wait for the stack to return **CREATION_COMPLETE** and then click the **Outputs** tab and record the database server IP address.

**Note:** In reality the IP would be a private address access via a VPN on Direct Connect.

</details>
