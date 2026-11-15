package br.ime.fatoutfitin.exception;

import org.springframework.http.HttpStatus;

/** Erro de negócio que vira uma resposta JSON com o status HTTP correspondente. */
public class ApiException extends RuntimeException {

    private final HttpStatus status;

    public ApiException(HttpStatus status, String mensagem) {
        super(mensagem);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public static ApiException badRequest(String mensagem) {
        return new ApiException(HttpStatus.BAD_REQUEST, mensagem);
    }

    public static ApiException notFound(String mensagem) {
        return new ApiException(HttpStatus.NOT_FOUND, mensagem);
    }
}
