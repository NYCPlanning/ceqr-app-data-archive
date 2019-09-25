REPOLOC="$(git rev-parse --show-toplevel)"

docker run -it --rm\
            -v $REPOLOC:/home/ceqr-app-data\
            -w /home/ceqr-app-data/\
            sptkl/docker-geosupport:19c bash -c "
            pip install -e .
            cd ceqr/recipes/dep_cats_permits && {
                pip install -r requirements.txt
                python build.py
            cd -;}
            "