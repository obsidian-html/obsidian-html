# once
pip install mkdocs markdown-callouts mkdocs-material

# new test setup
cd /tmp
mkdocs new my-project
cd my-project

cat <<EOT >> mkdocs.yml
theme:
  name: material
markdown_extensions:
  - callouts
EOT

cat <<EOT > docs/index.md
> EXAMPLE: This is a test   
> line two

End
EOT

mkdocs serve