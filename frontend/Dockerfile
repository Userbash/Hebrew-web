FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY public/ /usr/share/nginx/html/
# The Nginx config needs to be at /etc/nginx/nginx.conf, not in conf.d/default.conf, since the template provided is a full nginx.conf file.
COPY nginx.conf.template /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
