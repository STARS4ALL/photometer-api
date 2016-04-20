FROM node:4-onbuild
RUN npm install mongoose
RUN npm install body-parser
#CMD ["node", "server.js"]
EXPOSE 8888
