REPOLOC="$(git rev-parse --show-toplevel)"
START=$(date +%s);

docker run --rm\
            -v $REPOLOC:/home/ceqr-app-data\
            -w /home/ceqr-app-data/\
            -e RECIPE_ENGINE=$RECIPE_ENGINE\
            -e EDM_DATA=$EDM_DATA\
            -e CEQR_DATA=$CEQR_DATA\
            sptkl/docker-geosupport:latest bash -c "
            pip install -e .
            cd ceqr/recipes/sca_capacity_projects && {
                pip install -r requirements.txt
                python build.py
            cd -;}
            "

END=$(date +%s);
echo $((END-START)) | awk '{print int($1/60)" minutes and "int($1%60)" seconds elapsed."}'