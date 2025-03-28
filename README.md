# 🎵 Tidal Playlist Splitter

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A command-line tool that allows you to split a Tidal playlist into multiple segments and create new playlists with those segments. Perfect for creating more manageable chunks from large playlists or dividing playlists based on specific needs.

## ✨ Features

- Split any Tidal playlist into a specified number of segments
- Create new playlists automatically with customizable naming patterns
- Seamlessly authenticate with your Tidal account
- Customize playlist descriptions and naming conventions
- Simple and intuitive command-line interface

## 📋 Requirements

- Python 3.6 or higher
- `tidalapi` library
- Tidal account (Premium subscription recommended for the best experience)

## 🚀 Installation

1. Clone the repository or download the script:

```bash
git clone https://github.com/JoeCat1207/tidal-playlist-splitter.git
cd tidal-playlist-splitter
```

2. Install the required dependencies:

```bash
pip install tidalapi
```

## 🔧 Usage

### Basic usage:

```bash
python tidal_playlist_splitter.py https://listen.tidal.com/playlist/your-playlist-id
```

This will split the playlist into 2 segments (default) and create new playlists.

### Advanced usage:

```bash
python tidal_playlist_splitter.py https://listen.tidal.com/playlist/your-playlist-id --segments 5 --prefix "My Split" --naming-pattern "{prefix} {index} of {total} - {playlist}"
```

This will split the playlist into 5 segments and name them "My Split 1 of 5 - Original Playlist Name", etc.

## 📖 Command-line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `playlist_url` | (Required) | URL of the Tidal playlist to split |
| `--segments` | 2 | Number of segments to split the playlist into |
| `--prefix` | "Segment" | Prefix for the new playlist names |
| `--naming-pattern` | "{prefix} {index} - {playlist}" | Pattern for naming new playlists |
| `--description-pattern` | "Segment {index} of {total} from {playlist}" | Pattern for playlist descriptions |
|'--batch-size'|"NA"|"add any number behind this to specify batch sizing, will fix rate limit issues for extra long playlists"|

### Naming Pattern Variables:

- `{prefix}`: The prefix specified by the `--prefix` argument
- `{index}`: The segment number (1, 2, 3, etc.)
- `{total}`: The total number of segments
- `{playlist}`: The original playlist name

## 🔐 Authentication

The script uses Tidal's OAuth authentication. When you run the script:

1. A link will be provided in the console
2. Open this link in your browser
3. Log in to your Tidal account and authorize the application
4. The script will automatically detect when authentication is complete

## 📝 Examples

### Split a playlist into 3 equal parts:

```bash
python tidal_playlist_splitter.py https://listen.tidal.com/playlist/a0249e85-c4c3-41f5-895c-5b24243be473 --segments 3
```

### Create many small playlists with custom naming:

```bash
python tidal_playlist_splitter.py https://listen.tidal.com/playlist/a0249e85-c4c3-41f5-895c-5b24243be473 --segments 10 --prefix "Mini Mix" --naming-pattern "{prefix} #{index}: {playlist} Selections"
```

### Split a large playlist by albums (approximately):

```bash
python tidal_playlist_splitter.py https://listen.tidal.com/playlist/a0249e85-c4c3-41f5-895c-5b24243be473 --segments 61 --prefix "Album" --naming-pattern "{playlist} (Part {index} of {total})"
```

## ⚠️ Troubleshooting

- **Authentication Issues**: If you encounter authentication problems, try closing all Tidal instances in your browser and restarting the script.
- **Rate Limiting**: Tidal may rate-limit requests. If you encounter errors when creating many playlists, try increasing the delay between operations by modifying the script.
- **Library Version Compatibility**: This script works with recent versions of the tidalapi library. If you encounter issues, check your version with `pip show tidalapi` and consider updating.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions for improvements or bug fixes.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created with ❤️ for music lovers
