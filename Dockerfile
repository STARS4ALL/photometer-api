FROM node:4-onbuild

# update system
RUN apt-get update

# install python
RUN apt-get install -y software-properties-common
RUN python --version
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN pip install -U pip


# install python modules
RUN pip install deepdiff --user
RUN pip install geopy --user
RUN pip install deepdiff --user
RUN pip install attrdict --user

# add tess-grafana script configuration
#ADD config.json ./scripts/tess_grafana/

# run server
RUN npm install
CMD [ "npm", "start" ]

# port
EXPOSE 8888

# old recipe
#RUN npm install mongoose
#RUN npm install body-parser
##CMD ["node", "server.js"]
#EXPOSE 8888
