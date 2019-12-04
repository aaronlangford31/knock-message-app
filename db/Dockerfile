# A MySQL container.
FROM mysql:5.7
LABEL maintainer="Aaron Langford"

ADD init.sql /docker-entrypoint-initdb.d/

EXPOSE 3306
CMD ["mysqld"]
