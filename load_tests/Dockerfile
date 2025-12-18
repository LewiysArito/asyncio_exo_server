FROM golang:1.25.5 AS builder
RUN apt-get update &&\
    apt-get install -y git make ca-certificates &&\
    rm -rf /var/lib/apt/lists/*
RUN go install go.k6.io/xk6/cmd/xk6@latest
WORKDIR /work
COPY . /work
RUN xk6 build --with github.com/NAlexandrov/xk6-tcp@latest --output /work/k6

FROM alpine:3.18
RUN apk add --no-cache ca-certificates
COPY --from=builder /work/k6 /usr/bin/k6
WORKDIR /scripts
COPY . .
ENTRYPOINT ["/usr/bin/k6"]
CMD ["run", "tcp_test.js"]
