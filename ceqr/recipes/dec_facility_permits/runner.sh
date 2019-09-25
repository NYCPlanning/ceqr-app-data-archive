REPOLOC="$(git rev-parse --show-toplevel)"

docker run -it --rm\
            -v $REPOLOC:/home/ceqr-app-data\
            -w /home/ceqr-app-data/\
            sptkl/docker-geosupport:19c bash -c "
            pip install -e .
            cd ceqr/recipes/dec_facility_permits && {
                pip install -r requirements.txt
                python build.py
            cd -;}
            "
# cd $(dirname $0)

# python build.py