# Aquarium addon

![Aquariu addon for Ayon](https://storage.googleapis.com/fatfishlab-public/aquarium-studio-website/aquarium-ayon-logo.png)

> [!NOTE]
> This addon is ready to be used in production, but keep in mind that it isn't been tester heavily in a production environment.
> If you have any issue, feel free to reach us or directly open a new issue.

## Presentation

Welcome in [Aquarium](https://fatfi.sh/aquarium) addon for [Ayon](https://ynput.io/ayon/).

With this addon, you will be able to connect your projects from Ayon and Aquarium to synchronize your data.

This addon is composed by 3 main parts:

- [Client](#client)
- [Server](#server)
  - API
  - Frontend
- [Services](#services)
  - Leecher
  - Processor


### Directory structure

#### Client

Client code is used in the [Ayon Launcher](https://github.com/ynput/ayon-launcher), the AYON pipeline desktop application.

> [!WARNING]
> The client integration is not ready

This client integration allow you to

 - Authenticate the user
 - Publish media

#### Server

Python server-side part of the addon. It's mainly used to declare specific addon API endpoint, used by the leecher and processor services to keep your data in sync.

It's also responsible to expose specific addon settings, in your Ayon server and project settings.

##### Frontend

This folder is used to provide a web UI in your Ayon settings to pair projects between Ayon and Aquarium and also to trigger a full project sync.


#### Services

Syncing data between Ayon and Aquarium relies on [Ayon services system](https://ayon.ynput.io/docs/dev_event_system).

This addon use two components:

- **Leecher**
  - It's listenning Aquarium's events, and store them into Ayon database for async processing.
- **Processor**
  - It's looking for specific Aquarium events in Ayon's database and process them to transform data into compatible Ayon's structure and send request to addon server API endpoints to interact with the server.

## Installation

This addon is available in Ayon's addon market, or you can clone/download this repository to add it into your [Ayon server addon folder](https://ayon.ynput.io/docs/admin_server_installing_addons).

## Development

Looking to develop on this addon ?
First of all thanks !

We created a [dedicated documentation here](/docs/dev.md).

## Maintainers

The repository is co-maintained by [Ynput](https://ynput.io) and [Fatfish Lab](https://fatfi.sh)

We welcome new PR, so feel free to open new ones !

## License

This project uses the following license: Apache-2.0. See the license file to read it.