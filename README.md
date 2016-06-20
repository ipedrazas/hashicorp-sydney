# Hashicorp Meetup: Sydney



We're going to see how using Hashicorp Vault helps at mantaining our applications more secure and improves the reusability of all the different components.

Initial setup will be a running kubernetes cluster with Vault running as a pod. We will connect Vault to MySQL and then we will see how tokens and sidekick containers help to keep our code smaller and cleaner


# Setup

First things we need to do is to create a kubernetes cluster if you don't have one, we're going to use a Google Compute cluster:

	gcloud config set compute/zone europe-west1-d

	gcloud container --project "kube-1330" clusters create "vaultdemo" --zone "europe-west1-d" --machine-type "n1-standard-1" --scope "https://www.googleapis.com/auth/compute","https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management" --num-nodes "2" --network "default" --enable-cloud-logging --no-enable-cloud-monitoring

	gcloud container clusters get-credentials vaultdemo

Let's deploy a MySQL database first using Kubernetes Secrets:

	kubectl create secret generic mysql-pass --from-file=password.txt



Once we have the cluster up and running we have to deploy Vault. 

	kubectl create -f vault-deployment.yaml

This will create a Vault pod and a Vault service. We're using Vault in `dev` version, clearly, this is not a configuration suitable for production, but it will be enough to cover our demo.

Vault will start in `dev` mode, this means that our vault has been unsealed, so we need to get the root token:

	kubectl get pods
	kubectl logs VAULT_POD_NAME

We can see that the token is printed as part of the logs. Now, we have to access that Vault and create our policy:

	kubectl exec -it VAULT_POD_NAME sh
	export VAUL_ADDR=http://127.0.0.1:9000
	export VAULT_TOKEN=COPY_THE_TOKEN_FROM_THE_LOGS
	vault status

To create the policy `sydney-policy.json`, we're going to create a file

	cat policy.json <<EOF
	path "sys/*" {
	  policy = "deny"
	}

	path "secret/sydney/*" {
	  policy = "read"
	}

	path "mysql/creds/sydney" {
		capabilities = ["read", "list"]
	}
	EOF
	

Define the policy and generate a new token

	vault policy-write sydney policy.json
	vault token-create -policy=sydney

This will generate a new token, that it's the one we will use for our namespace.


Let's add a secret

	vault write secret/sydney password=meetup

Let's test
	
	vault read secret/sydney

Mount and initialise the `MySQL` backend

	vault mount mysql
	MYSQL_PASSWORD=$(cat password.txt)
	vault write mysql/config/conection connection_url="root:$MYSQL_PASSWORD@tcp(mysql:3306"
	vault write mysql/roles/sydney \
		sql="CREATE USER '{{name}}'@'%' IDENTIFIED_BY '{{password}}'; GRANT ALL PRIVILEGES on sydney.* TO '{{name}}'@'%';"

Let's test that everything works as expected:
	
	vault read mysql/creds/sydney



# Docker images

If you want to create the docker images yourself:

	docker build -t ipedrazas/vault -f Dockerfile.vault
