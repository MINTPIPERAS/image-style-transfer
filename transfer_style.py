# Standard Library Imports
from __future__ import print_function, division
from builtins import range
from datetime import datetime
from pathlib import Path
import uuid

# Third-Party Library Imports
import tensorflow as tf
import keras.backend as K
import numpy as np
from scipy.optimize import fmin_l_bfgs_b
from keras.models import Model
from keras.preprocessing.image import array_to_img

# Custom Module Imports
from models.vgg import vgg_avg_pool
from utils.image_utils import load_img_and_preprocess, preprocess_reverse
from utils.style_utils import style_loss

# ---- 模块级初始化（导入时执行一次） ----

# 禁用 TensorFlow 2.x 的 eager execution，兼容 Keras 1.x 风格的图计算
tf.compat.v1.disable_eager_execution()

# 启用 GPU 动态内存分配
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        print(e)

# ---- 常量 ----
CONTENT_WEIGHT = 1
STYLE_WEIGHTS = [1, 2, 3, 4]
DEFAULT_ITERATIONS = 10


def process_image(content_path, style_path, output_dir, iterations=DEFAULT_ITERATIONS, progress_callback=None):
    """
    执行神经风格迁移，将风格图的风格应用到内容图上。

    Args:
        content_path: 内容图片的文件路径
        style_path:  风格图片的文件路径
        output_dir:  输出目录路径
        iterations:  优化迭代次数 (默认 10)
        progress_callback: 可选回调函数，每轮迭代后调用，签名为 (iteration, total, loss)

    Returns:
        output_filename: 生成的结果文件名（不含目录路径）
    """
    content_path = str(content_path)
    style_path = str(style_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 加载并预处理图片（限制最大尺寸，防止超大图片导致内存溢出）
    MAX_DIM = 800  # VGG16 风格迁移在 400~800px 效果最佳，过大图片会 OOM
    content_img, _ = load_img_and_preprocess(content_path)
    h, w = content_img.shape[1:3]
    if max(h, w) > MAX_DIM:
        scale = MAX_DIM / max(h, w)
        h, w = int(h * scale), int(w * scale)
        content_img, _ = load_img_and_preprocess(content_path, (h, w))
        print(f"图片过大，已缩放到 {w}×{h}（最长边 {MAX_DIM}px）")
    style_img, _ = load_img_and_preprocess(style_path, (h, w))

    batch_shape = content_img.shape
    shape = content_img.shape[1:]

    # 2. 构建 VGG 模型
    vgg = vgg_avg_pool(shape[0], shape[1], shape[2])

    # 3. 内容特征提取（第7层捕获中间特征）
    content_model = Model(vgg.input, vgg.layers[7].output)
    content_target = K.variable(content_model.predict(content_img))

    # 4. 风格特征提取（所有 conv1 层）
    symbolic_conv_outputs = [
        layer.output for layer in vgg.layers if layer.name.endswith('conv1')
    ]
    style_model = Model(vgg.input, symbolic_conv_outputs)
    style_outputs = [K.variable(y) for y in style_model.predict(style_img)]

    # 5. 计算总损失：内容损失 + 风格损失
    loss = CONTENT_WEIGHT * K.mean(K.square(content_model.output - content_target))
    for w, symbolic, actual in zip(STYLE_WEIGHTS, symbolic_conv_outputs, style_outputs):
        loss += w * style_loss(symbolic[0], actual[0])

    # 6. 计算梯度
    gradients = K.gradients(loss, vgg.input)
    get_loss_and_gradients = K.function(
        inputs=[vgg.input],
        outputs=[loss] + gradients
    )

    def get_loss_and_gradients_wrapper(x_vector):
        """L-BFGS 优化器的包装函数，返回 loss 和梯度."""
        if not isinstance(x_vector, np.ndarray):
            raise TypeError("x_vector must be a numpy array")
        try:
            loss_value, gradients_value = get_loss_and_gradients(
                [x_vector.reshape(*batch_shape)]
            )
            return loss_value.astype(np.float64), gradients_value.flatten().astype(np.float64)
        except Exception as e:
            print("Error in get_loss_and_grads:", str(e))
            return None, None

    # 7. L-BFGS 优化
    t0 = datetime.now()
    x = np.random.randn(np.prod(batch_shape))

    for i in range(iterations):
        x, l, _ = fmin_l_bfgs_b(
            func=get_loss_and_gradients_wrapper,
            x0=x,
            maxfun=20
        )
        x = np.clip(x, -127, 127)
        if progress_callback:
            progress_callback(i + 1, iterations, float(l) if l is not None else 0.0)
        else:
            print("iter=%s, loss=%s" % (i, l))

    print("duration:", datetime.now() - t0)

    # 8. 还原预处理，生成最终图片
    generated_img = x.reshape(*batch_shape)
    stylized_img = preprocess_reverse(generated_img)
    result = stylized_img[0]

    # 裁剪到合法像素范围并转为 uint8
    result = np.clip(result, 0, 255).astype('uint8')

    # 9. 保存结果
    output_filename = f"styled_{uuid.uuid4().hex[:8]}.png"
    output_path = output_dir / output_filename
    result_img = array_to_img(result)
    result_img.save(str(output_path))

    print(f"Saved stylized image to: {output_path}")

    # 10. 清理 TF 图会话，防止下次调用时变量名冲突（graph mode 特有）
    K.clear_session()

    return output_filename
