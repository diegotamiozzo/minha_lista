$(document).ready(function() {
    // Pesquisa de material com indicador de carregamento
    $('#pesquisar-material').click(function() {
        const material = $('#material').val().trim();
        if (material === '') return;

        $(this).prop('disabled', true); // Desabilita botão enquanto pesquisa
        $('#resultados').html('<p class="text-info">Buscando...</p>');

        $.post('/pesquisar', { material: material }, function(data) {
            let resultadosHtml = '';

            if (data.length === 0) {
                resultadosHtml = '<p class="text-danger">Nenhum resultado encontrado.</p>';
            } else {
                data.forEach(function(item) {
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
        }).always(function() {
            $('#pesquisar-material').prop('disabled', false); // Reativa botão
        });
    });

    // Adicionando item à lista de itens selecionados com quantidade e unidade
    $(document).on('click', '.adicionar-item', function() {
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
                    <select name="itens_unidade" class="form-select form-select-sm">
                        <option value="Un">Un</option>
                        <option value="m">m</option>
                        <option value="kg">kg</option>
                        <option value="L">L</option>
                        <option value="L">Outros</option>
                    </select>
                </div>
                <input type="hidden" name="itens_codigo" value="${codigo}">
                <input type="hidden" name="itens_descricao" value="${descricao}">
            </div>
        `);

        // **Destaque o item já selecionado na lista**
        $(this).closest('.item-lista').addClass('bg-light text-muted').find('.adicionar-item').prop('disabled', true);

    });

    // Remover item da lista de itens selecionados
    $(document).on('click', '.remover-item', function() {
        const itemDiv = $(this).closest('.border.p-2.mb-2');
        const codigo = itemDiv.find('input[name="itens_codigo"]').val();

        // **Reativar na lista de pesquisa**
        $(`#resultados .item-lista[data-codigo="${codigo}"]`).removeClass('bg-light text-muted')
            .find('.adicionar-item').prop('disabled', false);

        itemDiv.fadeOut(300, function() { $(this).remove(); });
    });

    // Enviar o formulário para gerar o PDF
    $('#solicitacao-form').submit(function(e) {
        e.preventDefault();

        const itensSelecionados = $('#itens-selecionados input[name="itens_codigo"]').length;
        if (itensSelecionados === 0) {
            alert('Por favor, selecione pelo menos um item!');
            return;
        }

        const formData = $(this).serialize();

        $.post('/finalizar', formData, function(response) {
            if (response.message) {
                alert('PDF gerado com sucesso!');
                $('#baixar-pdf').show();
            } else {
                alert('Erro ao gerar PDF. Tente novamente.');
            }
        }).fail(function() {
            alert('Erro de comunicação com o servidor.');
        });
    });

    // Baixar o PDF e limpar o formulário
    $('#baixar-pdf').click(function() {
        window.location.href = '/baixar_pdf';

        setTimeout(function() {
            location.reload();
        }, 1000);
    });

// Garantir que o botão "Finalizar Seleção" funcione mesmo sem pesquisa de material
$('#finalizar-selecao').click(function() {
    $('#solicitacao-form').submit();

    // Limpar os resultados da pesquisa
    $('#resultados').empty();

    // Limpar o campo de entrada do material com um pequeno atraso
    setTimeout(function() {
        $('#material').val('');
    }, 50);
});

});
