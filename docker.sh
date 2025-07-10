docker run -d \
  --name jupyter-usuario1 \
  -e JUPYTER_TOKEN='usuario1token' \
  -p 0.0.0.0:8890:8888 \
  jupyter/base-notebook \
  start-notebook.sh \
    --NotebookApp.base_url=/usuario1/ \
    --NotebookApp.allow_origin='*' \
    --NotebookApp.tornado_settings='{"headers":{"Content-Security-Policy":""}}'