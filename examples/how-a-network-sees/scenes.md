# How a neural network sees, and how to fool it (about 1.5 min, EN + FA, text only, subtitles as .srt)

Visual first: each beat is written as the motion the eye follows, then the words (which go to the .srt).

## s00_title (S00Title)
0. **moves:** real pixel colours fly in and assemble the photo; title rises

## s01_pixels (S01Pixels)
0. **moves:** camera pushes into the nose; the real 8-bit RGB values of a 6x6 patch appear over the pixels
   **words:** To a neural network, this photo is a grid of numbers.
1. **moves:** camera pulls out; the photo splits into its red, green and blue planes, which slide apart in depth
   **words:** 224 by 224 pixels, 3 colours each: 150,528 numbers.

## s02_filters (S02Filters)
0. **moves:** the 64 real filters pop in as a grid, tile by tile; three that respond most lift out
   **words:** Its first layer has 64 small filters, learned from ImageNet.
1. **moves:** one filter sweeps the photo row by row while its feature map paints itself beside it
   **words:** Each filter slides across the image and lights up where its pattern appears.
2. **moves:** the three filters each drop onto their own map
   **words:** Three of the 64 maps.

## s03_layers (S03Layers)
0. **moves:** five fanned stacks of real channel maps, shrinking; particles stream through them; the camera tracks right
   **words:** Layer after layer, the maps get smaller and more numerous: from 64 maps of 112 by 112 to 512 maps of 7 by 7.

## s04_decision (S04Decision)
0. **moves:** the last stack collapses into a barcode of the 512 real pooled values
   **words:** The 512 maps are averaged into 512 numbers.
1. **moves:** the barcode streams into five probability bars that grow; the top one counts up to its value
   **words:** Those become a score for each of 1,000 classes. Golden retriever: 73.5%.

## s05_saliency (S05Saliency)
0. **moves:** the photo returns; a heat map washes over it from left to right
   **words:** Where is that answer most sensitive? Here.

## s06_gallery (S06Gallery)
0. **moves:** two photo cards fly in and flip to show their labels
   **words:** Other photos: goldfish, 98.4%. A tabby it calls Egyptian cat, 35.5%.
1. **moves:** a third card lands; its label is struck in red
   **words:** And sometimes it is wrong: this cat is a mousetrap, 49.1%.

## s07_attack (S07Attack)
0. **moves:** a shimmering change pattern (shown 64 times stronger) slides onto the photo
   **words:** Now change every pixel value by at most 2 out of 255.
1. **moves:** before and after side by side; a slider wipes between them
   **words:** To us, the photo looks the same.
2. **moves:** the bars from before re-sort: golden retriever drains, goldfish shoots to the top
   **words:** To the network, it is now a goldfish, with more than 99.99%.
3. **moves:** the caveat tags settle under the result
   **words:** One model, one photo, an attacker who knows the weights. Still: 2 out of 255 was enough.

## s08_close (S08Close)
0. **moves:** thumbnails of every asset fly out of experiments/network.py into a grid
   **words:** Every image here came from one script, run on real photos.

Claims: claims.json (c1-c6). Assets: experiments/fetch_images.py + experiments/network.py -> assets/ (manifest.json).