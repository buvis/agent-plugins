# PRD 00008: Export API

Status: draft.

## Problem

The accountant's tool wants to pull the orders itself instead of receiving a file.

## Must have

- M1. An authenticated endpoint returns the orders of a day as JSON.

## Acceptance

- A1. A request for a day returns its orders and a 200 status; an unknown day returns an empty list.
