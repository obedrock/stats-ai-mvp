FROM r-base:4.4.2

# Install system dependencies for R packages
# car needs LAPACK/BLAS/gfortran; nloptr needs cmake; fs needs libuv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    liblapack-dev \
    libblas-dev \
    gfortran \
    cmake \
    libuv1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages at build time (no network at runtime)
# Install in two steps: car and its dependencies first (most likely to fail),
# then the rest. This makes build failures easier to diagnose.
RUN Rscript -e "install.packages('car', repos='https://cran.rstudio.com/', Ncpus=2)"
RUN Rscript -e "install.packages(c('ggplot2','plotly','lmtest','sandwich','plm','forecast','tseries','jsonlite'), repos='https://cran.rstudio.com/', Ncpus=2)"

# Install security profile that disables system() and download.file()
COPY Rprofile.site /etc/R/Rprofile.site

# Create non-root user for R execution
RUN useradd -m -u 1000 ruser
USER ruser

# No CMD — caller provides Rscript command
