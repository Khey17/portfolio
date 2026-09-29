---
layout: post
title: "I Deployed AWS’s Official RAG Template on a Saturday"
date: 2026-03-23 12:00:00-0400
description: "A weekend with Amazon Bedrock, Elastic Cloud, and Terraform that turned into bugs in an official AWS sample and a PR back to the repo."
tags: aws rag terraform bedrock
categories: projects
published: true
related_posts: false
toc:
  sidebar: left
---

It was a Saturday. I got an email from AWS about a ready-to-deploy RAG pipeline template. Elastic Cloud for vector storage, AWS Lambda for orchestration, Terraform for deployment. The pitch was “skip weeks of integration work.”

I looked at the documentation, made a plan, and honestly thought this should be a piece of cake.

Spoiler: it was not.

I wanted to learn as I built, treat every step as something I could write down later. This post is that. The long version with every command is in the [README](https://github.com/Khey17/sample-patterns-for-aws-marketplace/blob/fix/aws-provider-version-constraint/solution-templates/elastic/end-to-end-rag-terraform/README.md). Original writeup is also on [Medium](https://medium.com/@karthikheyaa/i-deployed-awss-official-rag-template-on-a-saturday-here-s-what-actually-happened-8108641ededd).

## What even is a RAG pipeline?

Regular LLMs answer from training data. RAG is: upload your documents, store them in a searchable form, and when you ask a question the system pulls the relevant chunks and hands them to the model.

The picture that stuck:

> S3 is the filing cabinet. Elastic is the memory. Bedrock is the brain.

**Ingestion (documents go in):**

```
S3 upload → Lambda Vectorizer → Bedrock Titan Embeddings → Elastic Cloud (vector index)
```

**Query (questions come in):**

```
Your question → Elastic similarity search → Top relevant chunks → Bedrock LLM → Answer
```

Keyword search matches exact words. You search “car,” it finds “car.” Vector search matches meaning. You search “car,” it can still find “vehicle.” Embedding models turn text into numbers, and similar meanings sit close together. That is why RAG is actually useful.

## Terraform, in one analogy

AWS is the city. It owns the land, enforces the rules, and sends the bill.

Terraform is the architect: picks the region, lays the network, puts up Lambda, S3, API Gateway, and the PrivateLink tunnel to Elastic.

Docker is the interior: the code running inside Lambda.

```
terraform init    → downloads providers (like npm install)
terraform plan    → dry run, nothing gets built
terraform apply   → actually builds it
terraform destroy → tears it down
```

Two config values from me, 64 AWS resources. Someone packed weeks of AWS knowledge into a template. We just filled in the form. Except it did not deploy.

## The setup, before things broke

- AWS account with CLI configured
- Terraform ≥ 1.14.7
- Docker Desktop
- Git

Start Elastic Cloud from **AWS Marketplace**, not elastic.co. That is what makes PrivateLink work. Elasticsearch → Hosted → us-east-1.

Put Elastic credentials in Secrets Manager, not in a file that will end up in Git:

```bash
aws secretsmanager create-secret \
  --name "rag-elastic-credentials" \
  --region us-east-1 \
  --secret-string '{"username":"elastic","password":"YOUR_PASSWORD"}'
```

Then clone the template and `terraform init` → `plan` → `apply`.

Except it did not work. Not even close.

## The bugs

The template is from AWS. Official. On their GitHub. And it had issues that blocked deployment before a single resource was created.

**Version pin.** `terraform init` failed on the first try. The template pins the AWS provider to an exact version, but a module it pulls in needs a higher one. Those two constraints cannot coexist. One character change in two files (`>= 6.0.0` instead of `= 6.0.0`) fixes it. Finding which files took longer than the fix.

**Availability zone.** After that, the VPC endpoint failed. The template hardcoded `us-east-1a`. Elastic’s PrivateLink service does not run there, only in `b`, `c`, and `d`. I checked against AWS’s own API and put that in the PR.

**Private Lambda images.** The template points at a private ECR account your account cannot pull from. Recipe, no kitchen. I built the images from the included Dockerfiles and pushed them to my own ECR. The image is 3.3GB and Docker Desktop’s proxy kept dropping mid-upload. That part was not the template’s fault, just annoying. It got through after a few tries.

**Deprecated Bedrock model.** The agent Lambda had a model ID that no longer works. I swapped it for Amazon Nova Pro and had to parse the API Gateway body correctly (`json.loads` if it came in as a string).

I wrote the actual diffs in the [README](https://github.com/Khey17/sample-patterns-for-aws-marketplace/blob/fix/aws-provider-version-constraint/solution-templates/elastic/end-to-end-rag-terraform/README.md). The point is not the patches. The official template could not deploy out of the box. Better to know that before you spend a Saturday on it.

## And then it worked

After the Terraform version, the AZ mismatch, the 3.3GB Docker push, and the dead model ID, I uploaded a document to S3 and sent a query:

```bash
curl -X POST https://YOUR-API-URL/agent \
  -H "Content-Type: application/json" \
  -d '{"query": "What did Karth build on a Saturday?"}'
```

Response:

> Karth built a fully working RAG pipeline on a Saturday. This pipeline utilized AWS Bedrock, Elastic Cloud, Lambda, Terraform, and API Gateway.

That answer came from a document I uploaded. That moment was worth the frustrating hours.

I submitted [PR #43](https://github.com/aws-samples/sample-patterns-for-aws-marketplace/pull/43). At the time it was the first human PR in that repo. Everything else was Dependabot.

## What I actually learned

A **region** is a geographic area (`us-east-1` = Northern Virginia). An **availability zone** is a data center inside it (`a`, `b`, `c`, `d`). Services do not always run in every AZ. Always check.

Terraform is a config file that talks to AWS. You describe what you want, it figures out the order.

Do not put credentials in code. Secrets Manager is about $0.40/month per secret.

Docker + Lambda: build for `linux/amd64` even on Apple Silicon, and use `--provenance=false` with buildx or Lambda will reject the image.

Most errors in this project were solved by:

```bash
aws logs tail /aws/lambda/FUNCTION_NAME --follow
```

## Cost

NAT Gateways plus PrivateLink is about $3.50/day if you leave it up. Always `terraform destroy` when you are done. You can `apply` again later.

## Links

- [PR to the official AWS repo](https://github.com/aws-samples/sample-patterns-for-aws-marketplace/pull/43)
- [README with the fixes](https://github.com/Khey17/sample-patterns-for-aws-marketplace/blob/fix/aws-provider-version-constraint/solution-templates/elastic/end-to-end-rag-terraform/README.md)

Built on a Saturday. Took longer than expected. Worth it.
