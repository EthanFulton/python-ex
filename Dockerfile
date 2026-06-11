FROM image-registry.openshift-image-registry.svc:5000/base-images/sre-alpine:v01.00.01
 
LABEL version=v01.00.00-ethan \
      project=ethan-api
 
EXPOSE 8000
 
WORKDIR /app
 
# Copy the initial requirements.txt file to the container
COPY ./requirements.txt /app/requirements.txt
 
# Install necessary packages and dependencies
RUN sed -i 's/https/http/g' /etc/apk/repositories \
&& apk add --no-cache binutils libc-dev gcc libxslt-dev \
&& pip install --no-cache-dir -r requirements.txt \
&& chown -R sreadmin /app \
&& chgrp -R 0 /app \
&& chmod -R g=u /app
 
# Create new requirement file to check version used
RUN pip freeze > test-requirements.txt
 
# Optional: Copy the updated requirements.txt file to the host machine
# COPY ./test-requirements.txt /app/test-requirements.txt
 
 
# Set permissions
RUN chown -R sreadmin /app \
&& chgrp -R 0 /app \
&& chmod -R g=u /app
 
# Switch to non-root user
USER sreadmin
 
# Copy the rest of the application code
COPY --chown=sreadmin:app . /app
 
ENTRYPOINT ["gunicorn", "-b", ":8000", "-w 4", "api:app", "--timeout", "180", "--log-level", "DEBUG", "-p", "ca_api.pid"]