#!/bin/bash
echo "🪛 Installing VSCode Extensions:"
echo "--------------------------------"

# Docker 
extensions_list=(
    # Docker and remote tools
    #"ms-azuretools.vscode-docker"
    #"ms-vscode-remote.remote-containers"
    #"ms-kubernetes-tools.vscode-kubernetes-tools"
    #"ms-vscode-remote.vscode-remote-extensionpack"
    # Python tools
    "ms-python.python"
    "ms-python.vscode-python-envs"
    "ms-python.debugpy"
    "ms-python.vscode-pylance"
    "ms-python.isort"
    "ms-python.flake8"
    "ms-python.black-formatter"
    "charliermarsh.ruff"
    "ms-toolsai.jupyter"
    "ms-toolsai.jupyter-renderers"
    "ms-toolsai.vscode-jupyter-slideshow"
    "mechatroner.rainbow-csv"
    # Nix tools
    "bbenoist.Nix"
    # SQL
    "inferrinizzard.prettier-sql-vscode"
    # Yaml
    "redhat.vscode-yaml"
    # XML
    "redhat.vscode-xml"
    # Git and Github
    "GitHub.remotehub"
    "eamodio.gitlens"
    # Markdown
    "DavidAnson.vscode-markdownlint"
    "shd101wyy.markdown-preview-enhanced"
    # General code tools
    "njpwerner.autodocstring"
    "esbenp.prettier-vscode"
    "mikestead.dotenv"
    "ms-toolsai.datawrangler"
    "grapecity.gc-excelviewer"
    # Makefile
    "ms-vscode.makefile-tools"
)
for i in "${extensions_list[@]}"
do 
    code --install-extension "$i" --verbose
done