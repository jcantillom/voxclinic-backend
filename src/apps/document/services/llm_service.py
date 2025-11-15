import abc
import json
import logging
import os
import requests  # Necesario para llamar a la API REST de Ollama
from typing import Dict, Any, Union
from src.core.errors.errors import ConflictError

logger = logging.getLogger(__name__)


# Definición de la Interfaz del Motor LLM (Se mantiene inalterada)
class AbstractLLMEngine(abc.ABC):
    """
    Define la interfaz para cualquier motor de IA/LLM que estructure el dictado médico.
    """

    @abc.abstractmethod
    def structure_document(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """
        Toma la transcripción y los metadatos y devuelve el contenido estructurado final.
        """
        raise NotImplementedError


# Implementación de LLM: Ollama (Llama 3)
class OllamaLlmEngine(AbstractLLMEngine):
    """
    Implementación del motor LLM utilizando la API REST de Ollama para la inferencia
    de modelos Open Source (Llama 3).
    """

    def __init__(self):
        self.api_url = os.getenv("LLM_HOST_URL")
        self.model = os.getenv("LLM_MODEL_NAME")

        if not self.api_url or not self.model:
            logger.error("LLM_HOST_URL o LLM_MODEL_NAME no configurados.")
            raise ValueError("Configuración de LLM (Ollama) faltante. Revise su archivo .env.")

        # Endpoint específico para generación de contenido en Ollama
        self.generate_endpoint = f"{self.api_url}/generate"

    def _generate_prompt(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """Genera el prompt de sistema y las instrucciones para Llama 3."""

        # PROMPT AVANZADO: Instrucciones de rol para el LLM
        system_instruction = (
            "Usted es un experto en documentación médica que opera dentro de un ambiente de alta seguridad (HIPAA/ISO). "
            "Su tarea es corregir la transcripción de audio (que puede contener errores fonéticos, ejemplo: 'ante lo poste' por 'anteroposterior') "
            "a español médico **formal y correcto**, y luego estructurar el contenido en formato **Markdown**. "
            "La salida DEBE ser solo el contenido en Markdown, sin preámbulos ni encabezados de tipo 'Aquí está el informe'."
        )

        meta_info = json.dumps(clinical_meta, indent=2)

        # Instrucciones de estructura basadas en el tipo de documento
        if document_type == "radiology_report":
            instructions = (
                "Estructura el dictado como un Informe Radiológico profesional. "
                "Usa los siguientes encabezados en Markdown: "
                "1. **TÉCNICA** (si fue dictada, sino sugiere una común). "
                "2. **HALLAZGOS DETALLADOS**. "
                "3. **IMPRESIÓN DIAGNÓSTICA / CONCLUSIÓN**. "
                f"La transcripción es: '{transcript}'."
            )
        elif document_type == "clinical_history":
            instructions = (
                "Estructura el dictado para rellenar una Historia Clínica. "
                "Usa los siguientes encabezados en Markdown: "
                "1. **MOTIVO DE CONSULTA** (Extraer la razón principal). "
                "2. **ANAMNESIS DETALLADA**. "
                "3. **EXAMEN FÍSICO** (Si fue dictado). "
                "4. **PLAN MÉDICO Y TRATAMIENTO**. "
                f"La transcripción es: '{transcript}'."
            )
        else:
            instructions = (
                f"Estructura el dictado para el documento de tipo: {document_type.upper().replace('_', ' ')}. "
                "Corrige el lenguaje a español médico formal. Devuelve el texto corregido bajo un encabezado de **TRANSCRIPCIÓN MÉDICA CORREGIDA**. "
                f"La transcripción es: '{transcript}'."
            )

        final_prompt = f"""
SISTEMA: {system_instruction}

---
DATOS CLÍNICOS ADICIONALES:
{meta_info}
---
INSTRUCCIÓN ESPECÍFICA:
{instructions}
"""
        return final_prompt.strip()

    def structure_document(self, document_type: str, transcript: str, clinical_meta: Dict[str, Any]) -> str:
        """
        Llama a la API de Ollama para obtener el documento estructurado con Llama 3.
        """
        prompt = self._generate_prompt(document_type, transcript, clinical_meta)

        # Payload para la API de generación de Ollama
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # Desactivamos el streaming para obtener la respuesta completa
            "options": {
                "temperature": 0.01,  # Baja temperatura para alta precisión y consistencia
            }
        }

        try:
            logger.info(f"Llamando a Ollama (Llama 3) en {self.generate_endpoint} para {document_type}...")

            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=90  # 90 segundos para permitir inferencia lenta
            )
            response.raise_for_status()  # Lanza error para códigos HTTP 4xx/5xx

            data = response.json()

            # El campo 'response' contiene la salida del LLM
            generated_text = data.get("response", "").strip()

            if generated_text:
                return generated_text
            else:
                raise ConflictError("Respuesta de Llama 3 vacía o no generada correctamente.")

        except requests.exceptions.Timeout:
            logger.error("Timeout de la API de Ollama: La inferencia tardó demasiado.")
            raise ConflictError("Error en el motor LLM (Timeout): El servidor de Llama 3 tardó demasiado en responder.")
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión con Ollama en {self.generate_endpoint}. ¿Está el servicio corriendo?")
            raise ConflictError(
                "Error en el motor LLM: El servidor de Ollama no está corriendo. Verifique `ollama run llama3`.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de la API de Ollama: {e}")
            raise ConflictError(f"Error en el motor LLM (Ollama API): No se pudo generar el documento. Detalle: {e}")
        except Exception as e:
            logger.exception(f"Error inesperado al procesar la respuesta de Ollama: {e}")
            raise ConflictError(f"Error interno al procesar la respuesta del LLM. Detalle: {e}")

# Mantenemos MvpLlmEngine (Simulación) si lo necesita como fallback, o lo eliminamos.
# Para un proyecto real, lo eliminamos.