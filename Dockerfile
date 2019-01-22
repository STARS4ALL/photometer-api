FROM node:11.3

WORKDIR /usr/src/app
# update system
RUN apt-get update

# install python
RUN apt-get install -y software-properties-common
RUN python --version
RUN apt-get install -y python-dev
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN pip install -U pip


# install python modules
RUN pip install deepdiff --user
RUN pip install geopy --user
RUN pip install deepdiff --user
RUN pip install attrdict --user
RUN pip install requests --user
RUN pip install psutil --user

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./
# add tess-grafana script configuration
#ADD config.json ./scripts/tess_grafana/

# run server
RUN npm install
COPY . .
CMD [ "npm", "start" ]

# port
EXPOSE 8888

# old recipe
#RUN npm install mongoose
#RUN npm install body-parser
##CMD ["node", "server.js"]
#EXPOSE 8888
