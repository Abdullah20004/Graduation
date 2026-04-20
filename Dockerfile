# ------------------------------------------------------------------
#  SecureShop - DVWA-based Vulnerable E-Commerce Training Platform
# ------------------------------------------------------------------
FROM php:8.1-apache-bullseye

RUN echo 'Acquire::http::User-Agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)";' > /etc/apt/apt.conf.d/99waf-bypass \
    && apt-get update && apt-get install -y \
    mariadb-client \
    wget unzip \
    libmariadb-dev \
    python3 python3-pip \
    git netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# ---- Python requirements (Installed first for caching) ------------
WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install --default-timeout=1000 -r requirements.txt

# ---- PHP extensions -------------------------------------------------
RUN docker-php-ext-install mysqli pdo pdo_mysql

# ---- Working directory ----------------------------------------------
WORKDIR /var/www/html

# ---- Clean default Apache content -----------------------------------
RUN rm -rf /var/www/html/*

# ---- Copy full modified DVWA (your SecureShop base) -----------------
COPY dvwa/ /var/www/html/

# ---- Copy your custom SecureShop pages (overrides/extends DVWA) -----
COPY templates/ /app/templates/

# ---- Python & PHP generator scripts ---------------------------------
COPY generate_vulns.py /app/
COPY apply_vulns.php /app/
COPY requirements_docker.txt /app/requirements.txt
COPY api/dvwa_pages.py /app/api/dvwa_pages.py

# ---- Permissions ----------------------------------------------------
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && mkdir -p /var/www/html/config \
    && chown -R www-data:www-data /var/www/html/config \
    && chmod 777 /var/www/html/config \
    && chmod +x /app/generate_vulns.py

# ---- Apache / PHP tweaks --------------------------------------------
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf \
    && echo "allow_url_include=Off" >> /usr/local/etc/php/php.ini-production \
    && echo "allow_url_include=Off" >> /usr/local/etc/php/php.ini-development

# ---- Logs directory -------------------------------------------------
RUN mkdir -p /logs && chmod 777 /logs

# ---- Entrypoint -----------------------------------------------------
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]