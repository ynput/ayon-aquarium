# Aquarium addon services

If you didn't read [the addon presentation](../README.md#presentation), go check it out first to learn how this repository is structured.

## Start services for development

To start your service, go into each folder and run the commands:

- Duplicate the file `example_env` to `.env` file.
- Edit the `.env` with the `AYON_SERVER_URL` and `AYON_API_KEY`
  - You can reuse the same API KEY created when you setup your [dev envrionment](../docs/dev.md)
- `make build`
- `make dev`