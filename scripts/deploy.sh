#!/usr/bin/env bash
# Implanta a infraestrutura em duas passadas: a imagem precisa existir antes dos Cloud Run Jobs.
set -euo pipefail

cd "$(dirname "$0")/.."
: "${RADAR_PROJECT_ID:?defina RADAR_PROJECT_ID}"
REGION="${RADAR_REGION:-us-central1}"
TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"
TF_VERSION="${TF_VERSION:-1.9.8}"

# Alguns ambientes (inclusive certos Cloud Shell) trazem só um atalho que imprime instruções.
# Por isso a checagem exige a saída real do `terraform version`, não apenas o código de saída.
ensure_terraform() {
  if terraform version 2>/dev/null | grep -q '^Terraform v'; then
    return
  fi
  echo "Terraform não encontrado: instalando ${TF_VERSION} em ~/bin ..."
  mkdir -p "${HOME}/bin"
  curl -fsSL -o /tmp/terraform.zip \
    "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip"
  unzip -o -j /tmp/terraform.zip terraform -d "${HOME}/bin" >/dev/null
  chmod +x "${HOME}/bin/terraform"
  export PATH="${HOME}/bin:${PATH}"
  terraform version 2>/dev/null | grep -q '^Terraform v' || {
    echo "Falha ao instalar o Terraform." >&2
    exit 1
  }
}
ensure_terraform

terraform -chdir=infra init -input=false
terraform -chdir=infra apply -input=false -auto-approve -var "create_jobs=false"

IMAGE="${REGION}-docker.pkg.dev/${RADAR_PROJECT_ID}/radar/radar-alfabetizacao:${TAG}"
gcloud builds submit --project "${RADAR_PROJECT_ID}" --tag "${IMAGE}" .

terraform -chdir=infra apply -input=false -auto-approve -var "create_jobs=true" -var "image_tag=${TAG}"
echo "Pronto. Execute: gcloud run jobs execute radar-batch --region ${REGION} --wait"
