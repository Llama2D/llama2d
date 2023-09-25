#!/bin/bash

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is not installed. Please install it before running this script."
    exit 1
fi

# Directory containing the images
input_dir="."

# Output GIF file name
output_gif="output.gif"

# Check if the input directory exists
if [ ! -d "$input_dir" ]; then
    echo "Input directory not found: $input_dir"
    exit 1
fi

# Change to the input directory
cd "$input_dir" || exit

# Create the GIF from images 0.png through 8.png
convert -delay 100 -loop 0 {0..8}.png "$output_gif"

# Verify if the GIF creation was successful
if [ $? -eq 0 ]; then
    echo "GIF file created successfully: $output_gif"
else
    echo "Failed to create the GIF."
fi
