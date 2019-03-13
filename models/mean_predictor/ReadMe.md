## Push docker image to AWS

```sh push_to_aws.sh mean_predictor```

Train the model in the cloud and deploy it as sagemaker endpoint:

```bash
python train_deploy.py <args>
```

For argument description, call with --help or look at the script

## Running the model locally via docker

```bash
cd local_test
docker build  -t mean_predictor ../container
```

### Training locally
```bash
sh train_local.sh mean_predictor
```
The script will use the data provided in `test_dir/input/data/training/data.csv` for training.
The hyperparameters of the local model can be adjusted in `test_dir/input/config/hyperparameters.json`.

### Serving locally
```bash
sh serve_local.sh mean_predictor
```

Once the container is running locally, a REST-API will be exposed to the host system on port 8080.
Predictions can be made via POST request to localhost:8080/invocations

Example:
```bash
curl -d '{"start": "2019-01-28 00:05:00","end": "2019-02-10 00:20:00"}' -H "Content-Type: application/json" -X POST http:/localhost:8080/invocations
```

