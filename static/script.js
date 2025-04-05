$(document).ready(function () {
    // Pesquisa de material com indicador de carregamento
    $('#pesquisar-material').click(function () {
        const material = $('#material').val().trim();
        if (material === '') return;

        $(this).prop('disabled', true);
        $('#resultados').html('<p class="text-info">Buscando...</p>');

        $.post('/pesquisar', { material: material }, function (data) {
            let resultadosHtml = '';

            if (data.length === 0) {
                resultadosHtml = '<p class="text-danger">Nenhum resultado encontrado.</p>';
            } else {
                data.forEach(function (item) {
                    resultadosHtml += `
                        <div class="d-flex justify-content-between align-items-center border p-2 item-lista" 
                             data-codigo="${item.Codigo}" data-descricao="${item.Descricao}">
                            <span>${item.Codigo} - ${item.Descricao}</span>
                            <button type="button" class="btn btn-sm btn-success adicionar-item" 
                                data-codigo="${item.Codigo}" data-descricao="${item.Descricao}">
                                Selecionar
                            </button>
                        </div>
                    `;
                });
            }

            $('#resultados').html(resultadosHtml);
        }).always(function () {
            $('#pesquisar-material').prop('disabled', false);
        });
    });

    // Adicionar item com quantidade e unidade
    $(document).on('click', '.adicionar-item', function () {
        const codigo = $(this).data('codigo');
        const descricao = $(this).data('descricao');

        const itemExistente = $(`#itens-selecionados input[name="itens_codigo"][value="${codigo}"]`);
        if (itemExistente.length > 0) {
            itemExistente.closest('div').addClass('bg-warning');
            setTimeout(() => itemExistente.closest('div').removeClass('bg-warning'), 1000);
            return;
        }

        $('#itens-selecionados').append(`
            <div class="border p-2 mb-2 d-flex flex-column">
                <div class="d-flex justify-content-between align-items-center">
                    <span>${codigo} - ${descricao}</span>
                    <button type="button" class="btn btn-sm btn-danger remover-item">Remover</button>
                </div>
                <div class="d-flex mt-2">
                    <input type="number" name="itens_quantidade" class="form-control form-control-sm me-2" 
                        placeholder="Quantidade" min="1" required>
                    <select name="itens_unidade" class="form-select form-select-sm" required>
                        <option value="" disabled selected>Selecione</option>
                        <option value="Un">Un</option>
                        <option value="m">m</option>
                        <option value="kg">kg</option>
                        <option value="L">L</option>
                        <option value="Outros">Outros</option>
                    </select>
                </div>
                <input type="hidden" name="itens_codigo" value="${codigo}">
                <input type="hidden" name="itens_descricao" value="${descricao}">
            </div>
        `);

        $(this).closest('.item-lista').addClass('bg-light text-muted').find('.adicionar-item').prop('disabled', true);
    });

    // Remover item
    $(document).on('click', '.remover-item', function () {
        const itemDiv = $(this).closest('.border.p-2.mb-2');
        const codigo = itemDiv.find('input[name="itens_codigo"]').val();

        $(`#resultados .item-lista[data-codigo="${codigo}"]`).removeClass('bg-light text-muted')
            .find('.adicionar-item').prop('disabled', false);

        itemDiv.fadeOut(300, function () {
            $(this).remove();
        });
    });

    // Submeter formulário
    $('#solicitacao-form').submit(function (e) {
        e.preventDefault();

        const itensSelecionados = $('#itens-selecionados input[name="itens_codigo"]').length;
        if (itensSelecionados === 0) {
            alert('Por favor, selecione pelo menos um item!');
            return;
        }

        let formularioValido = true;

        // Verifica campos dinâmicos
        $('#itens-selecionados .border').each(function () {
            const quantidade = $(this).find('input[name="itens_quantidade"]').val();
            const unidade = $(this).find('select[name="itens_unidade"]').val();

            if (!quantidade || quantidade <= 0 || !unidade) {
                $(this).find('input[name="itens_quantidade"]').addClass('border border-danger');
                $(this).find('select[name="itens_unidade"]').addClass('border border-danger');
                formularioValido = false;
            } else {
                $(this).find('input[name="itens_quantidade"]').removeClass('border border-danger');
                $(this).find('select[name="itens_unidade"]').removeClass('border border-danger');
            }
        });

        // Verifica outros campos obrigatórios
        $('#solicitacao-form input[required], #solicitacao-form select[required]').each(function () {
            const isSelect = $(this).is('select');
            const value = $(this).val();

            if ((isSelect && !value) || (!isSelect && !value.trim())) {
                $(this).addClass('border border-danger');
                formularioValido = false;
            } else {
                $(this).removeClass('border border-danger');
            }
        });

        if (!formularioValido) {
            alert('Por favor, preencha todos os campos obrigatórios antes de enviar.');
            return;
        }

        const formData = $(this).serialize();

        $.post('/finalizar', formData, function (response) {
            if (response.message) {
                alert('PDF gerado com sucesso!');
                $('#baixar-pdf').show();
            } else {
                alert('Erro ao gerar PDF. Tente novamente.');
            }
        }).fail(function () {
            alert('Erro de comunicação com o servidor.');
        });
    });

    // Botão baixar PDF
    $('#baixar-pdf').click(function () {
        window.location.href = '/baixar_pdf';
        setTimeout(function () {
            location.reload();
        }, 1000);
    });

    // Finalizar seleção
    $('#finalizar-selecao').click(function () {
        $('#solicitacao-form').submit();
        $('#resultados').empty();
        setTimeout(function () {
            $('#material').val('');
        }, 50);
    });

    // Limpar material
    $('#limpar-material').click(function () {
        $('#material').val('');
        $('#resultados').fadeOut(200, function () {
            $(this).empty().show();
        });
    });

    // Remover borda vermelha ao preencher campos obrigatórios (inputs e selects)
    $('#solicitacao-form').on('input change', 'input[required], select[required]', function () {
        const tagName = $(this).prop('tagName').toLowerCase();
        const value = $(this).val();

        let isEmpty = false;

        if (tagName === 'select') {
            isEmpty = !value || value === '';
        } else {
            isEmpty = !value || value.trim() === '';
        }

        if (!isEmpty) {
            $(this).removeClass('border border-danger');
        }
    });

    // Remover borda vermelha ao preencher campos dos itens selecionados
    $('#itens-selecionados').on('input change', 'input[name="itens_quantidade"], select[name="itens_unidade"]', function () {
        const container = $(this).closest('.border');
        const quantidade = container.find('input[name="itens_quantidade"]').val();
        const unidade = container.find('select[name="itens_unidade"]').val();

        if (quantidade && quantidade > 0) {
            container.find('input[name="itens_quantidade"]').removeClass('border border-danger');
        }

        if (unidade && unidade !== '') {
            container.find('select[name="itens_unidade"]').removeClass('border border-danger');
        }
    });
});
