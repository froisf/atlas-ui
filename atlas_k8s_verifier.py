import uuid
import time
import subprocess
from kubernetes import client, config

class AtlasK8sVerifier:
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        self.batch_v1 = client.BatchV1Api()
        self.namespace = "atlas-agentic"

    def run_ephemeral_verifier(self, program_dir: str):
        job_name = f"verify-{uuid.uuid4().hex[:8]}"
        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job_name, "namespace": self.namespace},
            "spec": {
                "ttlSecondsAfterFinished": 120,
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [{
                            "name": "maven-verifier",
                            "image": "maven:3.9-eclipse-temurin-21",
                            "command": ["mvn", "clean", "test"],
                            "workingDir": "/app",
                            "volumeMounts": [{"name": "code-volume", "mountPath": "/app"}]
                        }],
                        "volumes": [{"name": "code-volume", "persistentVolumeClaim": {"claimName": "atlas-code-pvc"}}]
                    }
                }
            }
        }
        try:
            print(f"[K8s Verifier] Disparando Job {job_name} para {program_dir}...")
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job_manifest)
            print("[K8s Verifier] Aguardando execucao dos testes...")
            status_sucesso = False
            for _ in range(60):
                time.sleep(5)
                job_status = self.batch_v1.read_namespaced_job_status(name=job_name, namespace=self.namespace)
                if job_status.status.succeeded:
                    status_sucesso = True
                    break
                elif job_status.status.failed:
                    break
            if status_sucesso:
                return subprocess.CompletedProcess(args=["k8s", "mvn", "test"], returncode=0, stdout=" Testes OK", stderr="")
            else:
                return subprocess.CompletedProcess(args=["k8s", "mvn", "test"], returncode=1, stdout=" Falha nos testes", stderr="Erro")
        except Exception as e:
            print(f"[K8s Verifier] Erro critico: {e}")
            return subprocess.CompletedProcess(args=["k8s", "mvn", "test"], returncode=1, stdout="", stderr=str(e))
