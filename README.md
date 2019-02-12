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

1. Click the **Create Key Pair** button and enter a name for the *ks-keypair* for the demo. This will download the private key to your local machine.
    <p align="left">
      <img width="400" src="https://github.com/charliejllewellyn/aws-glue-quicksight-lab/blob/master/images/Create_key_pair.png">
    </p>

**Note** If you are running windows you need to follow [these instructions](https://aws.amazon.com/premiumsupport/knowledge-center/convert-pem-file-into-ppk/) to convert the key to putty.

</details>

<details>
<summary><strong>Deploy a database to mimic on-premesis</strong></summary><p>

To demonstrate the data being held in a different location we'll build our fake database in the Ireland region using CloudFormation.

| AWS Region | Short name | | 
| -- | -- | -- |
| EU West (Ireland) | eu-west-1 | [![cloudformation-launch-button](images/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=Production&templateURL=https://s3-eu-west-1.amazonaws.com/aws-shared-demo-cf-templates/fake-database/master_template.yaml) |
| EU West (Ireland) | eu-west-1 | <a href="https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=Production&templateURL=https://s3-eu-west-1.amazonaws.com/aws-shared-demo-cf-templates/fake-database/master_template.yaml" target="_blank" src="images/cloudformation-launch-stack.png"></a> |

</details>
