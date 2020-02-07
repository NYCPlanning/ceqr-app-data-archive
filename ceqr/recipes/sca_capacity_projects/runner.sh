REPOLOC="$(git rev-parse --show-toplevel)"
START=$(date +%s);

docker run -it --rm\
            -v $REPOLOC:/home/ceqr-app-data\
            -w /home/ceqr-app-data/\
            sptkl/docker-geosupport:19d bash -c "
            pip install -e .
            cd ceqr/recipes/sca_capacity_projects && {
                pip install -r requirements.txt
                python build.py
            cd -;}
            "

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)" minutes and "int($1%60)" seconds elapsed."}'