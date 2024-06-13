function filterProducts(category) {
    const productList = document.getElementById('product-list');
    const products = productList.querySelectorAll('.product');

    products.forEach(product => {
        if (category === 'all' || product.dataset.category === category) {
            product.style.display = 'block';
        } else {
            product.style.display = 'none';
        }
    });
}