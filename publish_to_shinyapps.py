# publish to shinyapps.io

install.packages("rsconnect-python")
install.packages("rsconnect")

if(!require("devtools"))
  install.packages("devtools")
devtools::install_github("posit-dev/rsconnect-python")
