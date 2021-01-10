# Script for installing BoolNet R package

SIMULATOR_VERSION = Sys.getenv('SIMULATOR_VERSION')
if (!require(devtools)) { 
  install.packages('devtools');
  require(devtools);
}
if (!require(BoolNet)) { 
  install_version('BoolNet', version=SIMULATOR_VERSION); 
  require(BoolNet);
} else {
  require(BoolNet);
  if (packageVersion('BoolNet') != SIMULATOR_VERSION) {
    install_version('BoolNet', version=SIMULATOR_VERSION);
    require(BoolNet);
  }
}
