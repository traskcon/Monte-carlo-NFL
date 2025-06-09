#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    https://shiny.posit.co/
#

library(shiny)
library(tidyverse)
library(ggplot2)
library(bslib)
library(bsicons)
library(RColorBrewer)
library(shinysky)
library(reticulate)

source_python("monte_carlo.py")