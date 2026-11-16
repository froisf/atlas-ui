import time
import uuid
from kubernetes import client, config

class AtlasK8sVerifier:
    def __init__(self, namespace="atlas-agentic"):
        self.namespace = namespace
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        self.batch_api = client.BatchV1Api()
        self.core_api = client.CoreV1Api()

    def run_ephemeral_verifier(self, source_code_java: str, test_code_junit: str) -> dict:
        job_id = f"atlas-verifier-{uuid.uuid4().hex[:8]}"
        job_manifest = {
            "apiVersion": "batch/v1", "kind": "Job",
            "metadata": {"name": job_id, "namespace": self.namespace},
            "spec": {
                "ttlSecondsAfterFinished": 120, "backoffLimit": 0,
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [{
                            "name": "maven-verifier",
                            "image": "maven:3.9.6-eclipse-temurin-21",
                            "command": ["/bin/sh", "-c"],
                            "args": [f"mkdir -p /app/src/main/java /app/src/test/java && echo '{source_code_java}' > /app/src/main/java/App.java && echo '{test_code_junit}' > /app/src/test/java/AppTest.java && cd /app && mvn test -DfailIfNoTests=true"]
                        }]
                    }
                }
            }
        }
        self.batch_api.create_namespaced_job(namespace=self.namespace, body=job_manifest)
        
        for _ in range(60):
            job = self.batch_api.read_namespaced_job_status(name=job_id, namespace=self.namespace)
            if job.status.succeeded:
                self.batch_api.delete_namespaced_job(name=job_id, namespace=self.namespace)
                return {"status": "SUCCESS", "message": "JUnit 5 100% GREEN"}
            elif job.status.failed:
                return {"status": "FAILED", "message": "Testes falharam no K8s"}
            time.sleep(5)
        return {"status": "TIMEOUT"}
