# Hashicorp Meetup: Sydney



We're going to see how using Hashicorp Vault helps at mantaining our applications more secure and improves the reusability of all the different components.

Initial setup will be a running kubernetes cluster with Vault running as a pod. We will connect Vault to MySQL and then we will see how tokens and sidekick containers help to keep our code smaller and cleaner


# Setup

First things we need to do is to create a kubernetes cluster if you don't have one, we're going to use a Google Compute cluster:

	gcloud config set compute/zone europe-west1-d

	gcloud container --project "kube-1330" clusters create "vaultdemo" --zone "europe-west1-d" --machine-type "n1-standard-1" --scope "https://www.googleapis.com/auth/compute","https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management" --num-nodes "2" --network "default" --enable-cloud-logging --no-enable-cloud-monitoring

	gcloud container clusters get-credentials vaultdemo

Let's deploy a MySQL database first using Kubernetes Secrets:

	echo -n "Hell0Sydney!" > password.txt
	kubectl create secret generic mysql-pass --from-file=password.txt
	kubectl create -f mysql-deploy.yaml

Let's test that our MySQL instance is working as expected. We will use a test pod to access the mysql service:

	kubectl create -f test-mysql.yaml

If we now hop into the container we will be able to connect to mysql:

	kubectl exec -it mysql-client bash

Now, we try to access the remote mysql:

	mysql -u root -h mysql -p

If everything has been done correctly, we should be in our mysql terminal. Let's take the opportunity to create our database and add some data. We will be using the script `sydney-db.sql`. Because the file is in our console, and we're inside of a container, it will be easier to copy & paste the script into the mysql term. Once finished, let's check that we do have data:

	select * from sydney;

Excellent, Vault time! exit your container and go back to the console. Once we have the cluster up and running we have to deploy Vault. 

	kubectl create -f vault-deployment.yaml

This will create a Vault pod and a Vault service. We're using Vault in `dev` version, clearly, this is not a configuration suitable for production, but it will be enough to cover our demo.

Vault will start in `dev` mode, this means that our vault has been unsealed, so we need to get the root token:

	kubectl get pods
	kubectl logs VAULT_POD_NAME

You should see something like this:

	ipedrazas@kube-1330:~$ kubectl logs vault-1525384569-tdbkj
	==> WARNING: Dev mode is enabled!

	In this mode, Vault is completely in-memory and unsealed.
	Vault is configured to only have a single unseal key. The root
	token has already been authenticated with the CLI, so you can
	immediately begin using the Vault CLI.
	The only step you need to take is to set the following
	environment variables:
	    export VAULT_ADDR='http://127.0.0.1:8200'
	The unseal key and root token are reproduced below in case you
	want to seal/unseal the Vault or play with authentication.
	Unseal Key: e001e8558eaa28c5baf45bc3fe2a81d4502dfde87c05a019f69d55121878ffe4
	Root Token: 19e9c532-e4af-5eec-9e85-cfff2f463e14
	==> Vault server configuration:
	                 Backend: inmem
	              Listener 1: tcp (addr: "127.0.0.1:8200", tls: "disabled")
	              Listener 2: tcp (addr: "0.0.0.0:9000", tls: "disabled")
	               Log Level: info
	                   Mlock: supported: true, enabled: false
	                 Version: Vault v0.6.0
	==> Vault server started! Log data will stream in below:
	2016/06/22 10:09:54 [INFO] core: security barrier not initialized
	2016/06/22 10:09:54 [INFO] core: security barrier initialized (shares: 1, threshold 1)
	2016/06/22 10:09:54 [INFO] core: post-unseal setup starting
	2016/06/22 10:09:54 [INFO] core: mounted backend of type generic at secret/
	2016/06/22 10:09:54 [INFO] core: mounted backend of type cubbyhole at cubbyhole/
	2016/06/22 10:09:54 [INFO] core: mounted backend of type system at sys/
	2016/06/22 10:09:54 [INFO] core: post-unseal setup complete
	2016/06/22 10:09:54 [INFO] core: root token generated
	2016/06/22 10:09:54 [INFO] core: pre-seal teardown starting
	2016/06/22 10:09:54 [INFO] rollback: starting rollback manager
	2016/06/22 10:09:54 [INFO] rollback: stopping rollback manager
	2016/06/22 10:09:54 [INFO] core: pre-seal teardown complete
	2016/06/22 10:09:54 [INFO] core: vault is unsealed
	2016/06/22 10:09:54 [INFO] core: post-unseal setup starting
	2016/06/22 10:09:54 [INFO] core: mounted backend of type generic at secret/
	2016/06/22 10:09:54 [INFO] core: mounted backend of type cubbyhole at cubbyhole/
	2016/06/22 10:09:54 [INFO] core: mounted backend of type system at sys/
	2016/06/22 10:09:54 [INFO] core: post-unseal setup complete
	2016/06/22 10:09:54 [INFO] rollback: starting rollback manager

We want to write down our root token:

	Root Token: 19e9c532-e4af-5eec-9e85-cfff2f463e14

We can see that the token is printed as part of the logs. Now, we have to access that Vault and create our policy:

	kubectl exec -it VAULT_POD_NAME sh
	export VAULT_ADDR=http://127.0.0.1:9000
	export VAULT_TOKEN=COPY_THE_TOKEN_FROM_YOUR_LOGS
	vault status

To create the policy `sydney-policy.json`, we're going to use a file located in the container in `/etc/policy.json`

	
	path "sys/*" {
	  policy = "deny"
	}

	path "secret/sydney/*" {
	  policy = "write"
	}

	path "mysql/creds/sydney" {
		capabilities = ["read", "list"]
	}
	

Define the policy and generate a new token

	vault policy-write sydney /etc/policy.json
	vault token-create -policy=sydney

This will generate a new token, that it's the one we will use for our namespace.

	/ # vault token-create -policy=sydney
	Key             Value
	---             -----
	token           9aa7bbc6-2a20-0f2b-dfff-6b57e0267ec4
	token_accessor  29990d59-6ad5-075a-2512-eabc5d35e9b8
	token_duration  2592000
	token_renewable true
	token_policies  [default sydney]

Let's add a secret

	vault write secret/sydney password=meetup

Let's test
	
	vault read secret/sydney


Let's mount our MySQL backend. What we want is to delegate on Vault the responsibility of managing the access to the database.

Mount and initialise the `MySQL` backend

	vault mount mysql
	vault write mysql/config/connection connection_url="root:Hell0Sydney!@tcp(mysql:3306)/"
	vault write mysql/roles/sydney \
    sql="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}';GRANT SELECT,INSERT ON *.* TO '{{name}}'@'%';"
    vault write mysql/roles/all \
    sql="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}';GRANT ALL ON *.* TO '{{name}}'@'%';"


to test is we can generate users, we can issue the following command:

	/ # vault read mysql/creds/sydney
	Key             Value
	---             -----
	lease_id        mysql/creds/sydney/ae56067c-e1c9-15ed-2d3e-71ce76d2aef7
	lease_duration  2592000
	lease_renewable true
	password        1f0d1ca4-1db2-ce98-cf53-538acf822d27
	username        root-a31ac088-47


Let's exit the container and create a secret for our namespace (in this example we're using the `Default` namespace but ideally you want to use a non-default one):

	echo -n "9aa7bbc6-2a20-0f2b-dfff-6b57e0267ec4" > token
	kubectl create secret generic vault --from-file=token


We're going to launch an very simple app that queries a Mysql database to fetch some data.

	kubectl create -f app-service.yaml
	kubectl create -f app-deploy.yaml

If we look at the deployment manifest of our app we will note that the pod has 2 containers:

* ipedrazas/meetup:sydney that runs our application
* ipedrazas/vault-helper:latest that runs a vault sidekick container





# Docker images

If you want to create the docker images yourself:

	docker build -t ipedrazas/vault -f Dockerfile.vault
